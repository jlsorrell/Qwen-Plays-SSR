using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Reflection.Emit;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;
using System.Text;

internal sealed class ParameterShape
{
    internal ParameterShape(string type) { Type = type; }
    internal string Type;
}

internal sealed class MethodShape
{
    internal MethodShape(MethodDefinitionHandle handle, string owner,
        string name, string visibility, bool isStatic, string returnType,
        ParameterShape[] parameters)
    {
        Handle = handle; Owner = owner; Name = name; Visibility = visibility;
        IsStatic = isStatic; ReturnType = returnType; Parameters = parameters;
    }
    internal MethodDefinitionHandle Handle;
    internal string Owner;
    internal string Name;
    internal string Visibility;
    internal bool IsStatic;
    internal string ReturnType;
    internal ParameterShape[] Parameters;
}

internal sealed class FieldShape
{
    internal FieldShape(string owner, string name, string visibility,
        bool isStatic, string fieldType)
    { Owner = owner; Name = name; Visibility = visibility; IsStatic = isStatic; FieldType = fieldType; }
    internal string Owner;
    internal string Name;
    internal string Visibility;
    internal bool IsStatic;
    internal string FieldType;
}

internal sealed class EnumShape
{
    internal EnumShape(string name, int value) { Name = name; Value = value; }
    internal string Name;
    internal int Value;
}

internal sealed class MethodCall
{
    internal MethodCall(int offset, string owner, string name,
        string returnType, string[] parameters)
    { Offset = offset; Owner = owner; Name = name; ReturnType = returnType; Parameters = parameters; }
    internal int Offset;
    internal string Owner;
    internal string Name;
    internal string ReturnType;
    internal string[] Parameters;
}

internal sealed class IlInstruction
{
    internal int Offset;
    internal OpCode OpCode;
    internal int Token;
    internal bool HasToken;
    internal int Int32Value;
    internal bool HasInt32;
    internal int VariableIndex;
    internal bool HasVariable;
    internal int BranchTarget;
    internal bool HasBranchTarget;
}

internal sealed class MethodParameterMetadata
{
    internal MethodParameterMetadata(string name, bool isOut)
    { Name = name; IsOut = isOut; }
    internal string Name;
    internal bool IsOut;
}

internal sealed class MetadataTypeProvider : ISignatureTypeProvider<string, object>
{
    public string GetArrayType(string elementType, ArrayShape shape)
    { return elementType + "[" + new string(',', shape.Rank - 1) + "]"; }
    public string GetByReferenceType(string elementType) { return elementType + "&"; }
    public string GetFunctionPointerType(MethodSignature<string> signature)
    { return "methodptr"; }
    public string GetGenericInstantiation(string genericType,
        ImmutableArray<string> typeArguments)
    {
        int tick = genericType.LastIndexOf('`');
        if (tick >= 0) genericType = genericType.Substring(0, tick);
        return genericType + "<" + String.Join(",", typeArguments) + ">";
    }
    public string GetGenericMethodParameter(object genericContext, int index)
    { return "!!" + index.ToString(CultureInfo.InvariantCulture); }
    public string GetGenericTypeParameter(object genericContext, int index)
    { return "!" + index.ToString(CultureInfo.InvariantCulture); }
    public string GetModifiedType(string modifier, string unmodifiedType, bool isRequired)
    { return unmodifiedType; }
    public string GetPinnedType(string elementType) { return elementType; }
    public string GetPointerType(string elementType) { return elementType + "*"; }
    public string GetPrimitiveType(PrimitiveTypeCode typeCode)
    {
        switch (typeCode)
        {
            case PrimitiveTypeCode.Boolean: return "System.Boolean";
            case PrimitiveTypeCode.Byte: return "System.Byte";
            case PrimitiveTypeCode.Char: return "System.Char";
            case PrimitiveTypeCode.Double: return "System.Double";
            case PrimitiveTypeCode.Int16: return "System.Int16";
            case PrimitiveTypeCode.Int32: return "System.Int32";
            case PrimitiveTypeCode.Int64: return "System.Int64";
            case PrimitiveTypeCode.IntPtr: return "System.IntPtr";
            case PrimitiveTypeCode.Object: return "System.Object";
            case PrimitiveTypeCode.SByte: return "System.SByte";
            case PrimitiveTypeCode.Single: return "System.Single";
            case PrimitiveTypeCode.String: return "System.String";
            case PrimitiveTypeCode.UInt16: return "System.UInt16";
            case PrimitiveTypeCode.UInt32: return "System.UInt32";
            case PrimitiveTypeCode.UInt64: return "System.UInt64";
            case PrimitiveTypeCode.UIntPtr: return "System.UIntPtr";
            case PrimitiveTypeCode.Void: return "System.Void";
            default: throw new BadImageFormatException("unsupported primitive");
        }
    }
    public string GetSZArrayType(string elementType) { return elementType + "[]"; }
    public string GetTypeFromDefinition(MetadataReader reader,
        TypeDefinitionHandle handle, byte rawTypeKind)
    { return MetadataImage.DefinitionName(reader, handle); }
    public string GetTypeFromReference(MetadataReader reader,
        TypeReferenceHandle handle, byte rawTypeKind)
    { return MetadataImage.ReferenceName(reader, handle); }
    public string GetTypeFromSpecification(MetadataReader reader, object genericContext,
        TypeSpecificationHandle handle, byte rawTypeKind)
    { return reader.GetTypeSpecification(handle).DecodeSignature(this, genericContext); }
}

internal sealed class MetadataImage : IDisposable
{
    private static readonly Dictionary<ushort, OpCode> Opcodes = BuildOpcodes();
    private readonly FileStream stream;
    private readonly PEReader pe;
    private readonly MetadataTypeProvider provider = new MetadataTypeProvider();

    private MetadataImage(FileStream stream, PEReader pe)
    { this.stream = stream; this.pe = pe; Reader = pe.GetMetadataReader(); }
    internal MetadataReader Reader { get; private set; }
    internal PEHeaders Headers { get { return pe.PEHeaders; } }

    internal static MetadataImage Open(string path, string option)
    {
        if (String.IsNullOrEmpty(path)) throw new ArgumentException(option + " is required");
        if (!Path.IsPathRooted(path)) throw new ArgumentException(option + " must be absolute");
        FileStream stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
        try
        {
            PEReader pe = new PEReader(stream, PEStreamOptions.LeaveOpen);
            if (!pe.HasMetadata) throw new BadImageFormatException("managed metadata is required");
            return new MetadataImage(stream, pe);
        }
        catch { stream.Dispose(); throw; }
    }

    public void Dispose() { pe.Dispose(); stream.Dispose(); }

    internal static string DefinitionName(MetadataReader reader, TypeDefinitionHandle handle)
    {
        TypeDefinition definition = reader.GetTypeDefinition(handle);
        string name = reader.GetString(definition.Name);
        TypeDefinitionHandle parent = definition.GetDeclaringType();
        if (!parent.IsNil) return DefinitionName(reader, parent) + "." + name;
        string typeNamespace = reader.GetString(definition.Namespace);
        return typeNamespace.Length == 0 ? name : typeNamespace + "." + name;
    }

    internal static string ReferenceName(MetadataReader reader, TypeReferenceHandle handle)
    {
        TypeReference reference = reader.GetTypeReference(handle);
        string name = reader.GetString(reference.Name);
        if (reference.ResolutionScope.Kind == HandleKind.TypeReference)
            return ReferenceName(reader, (TypeReferenceHandle)reference.ResolutionScope) + "." + name;
        string typeNamespace = reader.GetString(reference.Namespace);
        return typeNamespace.Length == 0 ? name : typeNamespace + "." + name;
    }

    internal string TypeName(EntityHandle handle)
    {
        if (handle.Kind == HandleKind.TypeDefinition) return DefinitionName(Reader, (TypeDefinitionHandle)handle);
        if (handle.Kind == HandleKind.TypeReference) return ReferenceName(Reader, (TypeReferenceHandle)handle);
        if (handle.Kind == HandleKind.TypeSpecification)
            return Reader.GetTypeSpecification((TypeSpecificationHandle)handle).DecodeSignature(provider, null);
        throw new BadImageFormatException("unsupported type handle");
    }

    internal TypeDefinitionHandle FindType(string name)
    {
        TypeDefinitionHandle found = default(TypeDefinitionHandle);
        foreach (TypeDefinitionHandle handle in Reader.TypeDefinitions)
        {
            if (DefinitionName(Reader, handle) != name) continue;
            if (!found.IsNil) throw new InvalidOperationException("duplicate type: " + name);
            found = handle;
        }
        if (found.IsNil) throw new InvalidOperationException("missing type: " + name);
        return found;
    }

    internal MethodShape[] Methods(string owner, string name)
    {
        TypeDefinition definition = Reader.GetTypeDefinition(FindType(owner));
        List<MethodShape> result = new List<MethodShape>();
        foreach (MethodDefinitionHandle handle in definition.GetMethods())
        {
            MethodDefinition method = Reader.GetMethodDefinition(handle);
            if (Reader.GetString(method.Name) != name) continue;
            result.Add(Shape(owner, handle, method));
        }
        return result.ToArray();
    }

    internal MethodShape[] AllMethods(string owner)
    {
        TypeDefinition definition = Reader.GetTypeDefinition(FindType(owner));
        List<MethodShape> result = new List<MethodShape>();
        foreach (MethodDefinitionHandle handle in definition.GetMethods())
            result.Add(Shape(owner, handle, Reader.GetMethodDefinition(handle)));
        return result.ToArray();
    }

    internal string[] AllTypeNames()
    {
        List<string> result = new List<string>();
        foreach (TypeDefinitionHandle handle in Reader.TypeDefinitions)
            result.Add(DefinitionName(Reader, handle));
        return result.ToArray();
    }

    internal MethodParameterMetadata[] ParameterMetadata(MethodShape shape)
    {
        MethodDefinition method = Reader.GetMethodDefinition(shape.Handle);
        MethodParameterMetadata[] result =
            new MethodParameterMetadata[shape.Parameters.Length];
        foreach (ParameterHandle handle in method.GetParameters())
        {
            Parameter parameter = Reader.GetParameter(handle);
            if (parameter.SequenceNumber == 0) continue;
            int index = parameter.SequenceNumber - 1;
            result[index] = new MethodParameterMetadata(
                Reader.GetString(parameter.Name),
                (parameter.Attributes & ParameterAttributes.Out) != 0);
        }
        for (int index = 0; index < result.Length; index++)
            if (result[index] == null)
                result[index] = new MethodParameterMetadata("", false);
        return result;
    }

    internal bool HasTypeAttribute(string owner, string attributeType)
    {
        TypeDefinition definition = Reader.GetTypeDefinition(FindType(owner));
        foreach (CustomAttributeHandle handle in definition.GetCustomAttributes())
            if (AttributeType(handle) == attributeType) return true;
        return false;
    }

    internal string[] TypeAttributeStrings(string owner, string attributeType)
    {
        TypeDefinition definition = Reader.GetTypeDefinition(FindType(owner));
        foreach (CustomAttributeHandle handle in definition.GetCustomAttributes())
        {
            if (AttributeType(handle) != attributeType) continue;
            BlobReader value = Reader.GetBlobReader(
                Reader.GetCustomAttribute(handle).Value);
            if (value.ReadUInt16() != 1)
                throw new BadImageFormatException("invalid custom attribute prolog");
            List<string> strings = new List<string>();
            while (value.RemainingBytes > 2)
                strings.Add(value.ReadSerializedString());
            if (value.RemainingBytes != 2 || value.ReadUInt16() != 0)
                throw new BadImageFormatException("custom attribute has named arguments");
            return strings.ToArray();
        }
        throw new InvalidOperationException("missing attribute: " + attributeType);
    }

    internal string[] AssemblyReferences()
    {
        List<string> result = new List<string>();
        foreach (AssemblyReferenceHandle handle in Reader.AssemblyReferences)
            result.Add(Reader.GetString(Reader.GetAssemblyReference(handle).Name));
        result.Sort(StringComparer.Ordinal);
        return result.ToArray();
    }

    internal string StringConstant(string owner, string name)
    {
        TypeDefinition definition = Reader.GetTypeDefinition(FindType(owner));
        foreach (FieldDefinitionHandle handle in definition.GetFields())
        {
            FieldDefinition field = Reader.GetFieldDefinition(handle);
            if (Reader.GetString(field.Name) != name) continue;
            Constant constant = Reader.GetConstant(field.GetDefaultValue());
            if (constant.TypeCode != ConstantTypeCode.String)
                throw new InvalidOperationException("constant is not a string");
            BlobReader value = Reader.GetBlobReader(constant.Value);
            return value.ReadUTF16(value.RemainingBytes);
        }
        throw new InvalidOperationException("missing constant: " + owner + "." + name);
    }

    private string AttributeType(CustomAttributeHandle handle)
    {
        EntityHandle constructor = Reader.GetCustomAttribute(handle).Constructor;
        if (constructor.Kind == HandleKind.MemberReference)
        {
            MemberReference member = Reader.GetMemberReference(
                (MemberReferenceHandle)constructor);
            return TypeName((EntityHandle)member.Parent);
        }
        if (constructor.Kind == HandleKind.MethodDefinition)
        {
            MethodDefinition method = Reader.GetMethodDefinition(
                (MethodDefinitionHandle)constructor);
            return DefinitionName(Reader, method.GetDeclaringType());
        }
        throw new BadImageFormatException("invalid attribute constructor");
    }

    private MethodShape Shape(string owner, MethodDefinitionHandle handle,
        MethodDefinition method)
    {
        MethodSignature<string> signature = method.DecodeSignature(provider, null);
        ParameterShape[] parameters = new ParameterShape[signature.ParameterTypes.Length];
        for (int index = 0; index < parameters.Length; index++)
            parameters[index] = new ParameterShape(signature.ParameterTypes[index]);
        return new MethodShape(handle, owner, Reader.GetString(method.Name),
            MethodVisibility(method.Attributes),
            (method.Attributes & MethodAttributes.Static) != 0,
            signature.ReturnType, parameters);
    }

    internal FieldShape[] Fields(string owner, string name)
    {
        TypeDefinition definition = Reader.GetTypeDefinition(FindType(owner));
        List<FieldShape> result = new List<FieldShape>();
        foreach (FieldDefinitionHandle handle in definition.GetFields())
        {
            FieldDefinition field = Reader.GetFieldDefinition(handle);
            if (Reader.GetString(field.Name) != name) continue;
            result.Add(new FieldShape(owner, name, FieldVisibility(field.Attributes),
                (field.Attributes & FieldAttributes.Static) != 0,
                field.DecodeSignature(provider, null)));
        }
        return result.ToArray();
    }

    internal int EnumValue(string owner, string name)
    {
        TypeDefinition definition = Reader.GetTypeDefinition(FindType(owner));
        foreach (FieldDefinitionHandle handle in definition.GetFields())
        {
            FieldDefinition field = Reader.GetFieldDefinition(handle);
            if (Reader.GetString(field.Name) != name) continue;
            if ((field.Attributes & (FieldAttributes.Public | FieldAttributes.Static | FieldAttributes.Literal))
                != (FieldAttributes.Public | FieldAttributes.Static | FieldAttributes.Literal)
                || field.DecodeSignature(provider, null) != owner)
                throw new InvalidOperationException("invalid enum shape: " + name);
            ConstantHandle constantHandle = field.GetDefaultValue();
            if (constantHandle.IsNil) throw new InvalidOperationException("missing enum value: " + name);
            Constant constant = Reader.GetConstant(constantHandle);
            if (constant.TypeCode != ConstantTypeCode.Int32) throw new InvalidOperationException("wrong enum type: " + name);
            BlobReader bytes = Reader.GetBlobReader(constant.Value);
            int value = bytes.ReadInt32();
            if (bytes.RemainingBytes != 0) throw new BadImageFormatException("trailing enum bytes");
            return value;
        }
        throw new InvalidOperationException("missing enum: " + name);
    }

    internal List<IlInstruction> Instructions(MethodShape shape)
    {
        MethodDefinition definition = Reader.GetMethodDefinition(shape.Handle);
        if (definition.RelativeVirtualAddress == 0) return new List<IlInstruction>();
        ImmutableArray<byte> bytes = pe.GetMethodBody(definition.RelativeVirtualAddress).GetILContent();
        List<IlInstruction> result = new List<IlInstruction>();
        int offset = 0;
        while (offset < bytes.Length)
        {
            int instructionOffset = offset;
            ushort value = bytes[offset++];
            if (value == 0xfe) { RequireBytes(bytes, offset, 1); value = (ushort)(0xfe00 | bytes[offset++]); }
            OpCode opCode;
            if (!Opcodes.TryGetValue(value, out opCode)) throw new BadImageFormatException("unknown opcode");
            IlInstruction instruction = new IlInstruction { Offset = instructionOffset, OpCode = opCode };
            int size = OperandSize(bytes, offset, opCode.OperandType);
            RequireBytes(bytes, offset, size);
            if (opCode.OperandType == OperandType.ShortInlineI)
            { instruction.HasInt32 = true; instruction.Int32Value = unchecked((sbyte)bytes[offset]); }
            else if (opCode.OperandType == OperandType.InlineI)
            { instruction.HasInt32 = true; instruction.Int32Value = ReadInt32(bytes, offset); }
            else if (opCode.OperandType == OperandType.InlineMethod
                || opCode.OperandType == OperandType.InlineField
                || opCode.OperandType == OperandType.InlineString
                || opCode.OperandType == OperandType.InlineTok
                || opCode.OperandType == OperandType.InlineType)
            { instruction.HasToken = true; instruction.Token = ReadInt32(bytes, offset); }
            else if (opCode.OperandType == OperandType.ShortInlineVar)
            { instruction.HasVariable = true; instruction.VariableIndex = bytes[offset]; }
            else if (opCode.OperandType == OperandType.InlineVar)
            { instruction.HasVariable = true; instruction.VariableIndex = bytes[offset] | (bytes[offset + 1] << 8); }
            else if (opCode.OperandType == OperandType.ShortInlineBrTarget)
            {
                instruction.HasBranchTarget = true;
                instruction.BranchTarget = offset + size + unchecked((sbyte)bytes[offset]);
            }
            else if (opCode.OperandType == OperandType.InlineBrTarget)
            {
                instruction.HasBranchTarget = true;
                instruction.BranchTarget = offset + size + ReadInt32(bytes, offset);
            }
            result.Add(instruction);
            offset += size;
        }
        return result;
    }

    internal List<MethodCall> Calls(MethodShape shape)
    {
        List<MethodCall> result = new List<MethodCall>();
        List<IlInstruction> instructions = Instructions(shape);
        for (int index = 0; index < instructions.Count; index++)
        {
            IlInstruction instruction = instructions[index];
            if (!instruction.HasToken || (instruction.OpCode.Value != OpCodes.Call.Value
                && instruction.OpCode.Value != OpCodes.Callvirt.Value
                && instruction.OpCode.Value != OpCodes.Newobj.Value)) continue;
            result.Add(ResolveCall(instruction.Offset, instruction.Token));
        }
        return result;
    }

    private MethodCall ResolveCall(int offset, int token)
    {
        EntityHandle handle = System.Reflection.Metadata.Ecma335.MetadataTokens.EntityHandle(token);
        if (handle.Kind == HandleKind.MethodSpecification)
            handle = Reader.GetMethodSpecification(
                (MethodSpecificationHandle)handle).Method;
        if (handle.Kind == HandleKind.MethodDefinition)
        {
            MethodDefinition method = Reader.GetMethodDefinition((MethodDefinitionHandle)handle);
            MethodSignature<string> signature = method.DecodeSignature(provider, null);
            return new MethodCall(offset, DefinitionName(Reader, method.GetDeclaringType()),
                Reader.GetString(method.Name), signature.ReturnType, Copy(signature.ParameterTypes));
        }
        if (handle.Kind == HandleKind.MemberReference)
        {
            MemberReference member = Reader.GetMemberReference((MemberReferenceHandle)handle);
            MethodSignature<string> signature = member.DecodeMethodSignature(provider, null);
            return new MethodCall(offset, TypeName((EntityHandle)member.Parent),
                Reader.GetString(member.Name), signature.ReturnType, Copy(signature.ParameterTypes));
        }
        throw new BadImageFormatException("call is not a method");
    }

    internal string TokenType(IlInstruction instruction)
    {
        if (!instruction.HasToken)
            throw new InvalidOperationException("instruction has no token");
        EntityHandle handle = System.Reflection.Metadata.Ecma335.MetadataTokens
            .EntityHandle(instruction.Token);
        return TypeName(handle);
    }

    internal string StringLiteral(IlInstruction instruction)
    {
        if (!instruction.HasToken
            || instruction.OpCode.Value != OpCodes.Ldstr.Value)
            throw new InvalidOperationException("instruction is not ldstr");
        UserStringHandle handle = System.Reflection.Metadata.Ecma335.MetadataTokens
            .UserStringHandle(instruction.Token & 0x00ffffff);
        return Reader.GetUserString(handle);
    }

    internal string FieldName(IlInstruction instruction)
    {
        if (!instruction.HasToken)
            throw new InvalidOperationException("instruction has no field token");
        EntityHandle handle = System.Reflection.Metadata.Ecma335.MetadataTokens
            .EntityHandle(instruction.Token);
        if (handle.Kind == HandleKind.FieldDefinition)
            return Reader.GetString(Reader.GetFieldDefinition(
                (FieldDefinitionHandle)handle).Name);
        if (handle.Kind == HandleKind.MemberReference)
            return Reader.GetString(Reader.GetMemberReference(
                (MemberReferenceHandle)handle).Name);
        throw new BadImageFormatException("token is not a field");
    }

    internal MethodShape MethodFromToken(IlInstruction instruction)
    {
        if (!instruction.HasToken)
            throw new InvalidOperationException("instruction has no method token");
        EntityHandle handle = System.Reflection.Metadata.Ecma335.MetadataTokens
            .EntityHandle(instruction.Token);
        if (handle.Kind != HandleKind.MethodDefinition)
            throw new BadImageFormatException("delegate target is not a method definition");
        MethodDefinitionHandle methodHandle = (MethodDefinitionHandle)handle;
        MethodDefinition method = Reader.GetMethodDefinition(methodHandle);
        string owner = DefinitionName(Reader, method.GetDeclaringType());
        return Shape(owner, methodHandle, method);
    }

    internal MethodCall MethodTokenCall(IlInstruction instruction)
    {
        if (!instruction.HasToken)
            throw new InvalidOperationException("instruction has no method token");
        return ResolveCall(instruction.Offset, instruction.Token);
    }

    internal static bool TryConstant(IlInstruction instruction, out int value)
    {
        value = 0;
        short opcode = instruction.OpCode.Value;
        if (opcode == OpCodes.Ldc_I4_0.Value) return true;
        if (opcode == OpCodes.Ldc_I4_M1.Value) { value = -1; return true; }
        if (opcode == OpCodes.Ldc_I4_1.Value) { value = 1; return true; }
        if (opcode == OpCodes.Ldc_I4_2.Value) { value = 2; return true; }
        if (opcode == OpCodes.Ldc_I4_3.Value) { value = 3; return true; }
        if (opcode == OpCodes.Ldc_I4_4.Value) { value = 4; return true; }
        if (opcode == OpCodes.Ldc_I4_5.Value) { value = 5; return true; }
        if (opcode == OpCodes.Ldc_I4_6.Value) { value = 6; return true; }
        if (opcode == OpCodes.Ldc_I4_7.Value) { value = 7; return true; }
        if (opcode == OpCodes.Ldc_I4_8.Value) { value = 8; return true; }
        if (instruction.HasInt32) { value = instruction.Int32Value; return true; }
        return false;
    }

    internal static bool TryArgumentIndex(
        IlInstruction instruction, out int value)
    {
        value = 0;
        short opcode = instruction.OpCode.Value;
        if (opcode == OpCodes.Ldarg_0.Value) return true;
        if (opcode == OpCodes.Ldarg_1.Value) { value = 1; return true; }
        if (opcode == OpCodes.Ldarg_2.Value) { value = 2; return true; }
        if (opcode == OpCodes.Ldarg_3.Value) { value = 3; return true; }
        if ((opcode == OpCodes.Ldarg.Value || opcode == OpCodes.Ldarg_S.Value)
            && instruction.HasVariable)
        { value = instruction.VariableIndex; return true; }
        return false;
    }

    private static string[] Copy(ImmutableArray<string> values)
    { string[] copy = new string[values.Length]; for (int i = 0; i < copy.Length; i++) copy[i] = values[i]; return copy; }
    private static string MethodVisibility(MethodAttributes value)
    { MethodAttributes access = value & MethodAttributes.MemberAccessMask; return access == MethodAttributes.Public ? "public" : access == MethodAttributes.Private ? "private" : access == MethodAttributes.Assembly ? "assembly" : "other"; }
    private static string FieldVisibility(FieldAttributes value)
    { FieldAttributes access = value & FieldAttributes.FieldAccessMask; return access == FieldAttributes.Public ? "public" : access == FieldAttributes.Private ? "private" : access == FieldAttributes.Assembly ? "assembly" : "other"; }
    private static Dictionary<ushort, OpCode> BuildOpcodes()
    { Dictionary<ushort, OpCode> result = new Dictionary<ushort, OpCode>(); FieldInfo[] fields = typeof(OpCodes).GetFields(BindingFlags.Public | BindingFlags.Static); for (int i = 0; i < fields.Length; i++) if (fields[i].FieldType == typeof(OpCode)) { OpCode code = (OpCode)fields[i].GetValue(null); result[unchecked((ushort)code.Value)] = code; } return result; }
    private static int OperandSize(ImmutableArray<byte> bytes, int offset, OperandType type)
    { switch (type) { case OperandType.InlineNone: return 0; case OperandType.ShortInlineBrTarget: case OperandType.ShortInlineI: case OperandType.ShortInlineVar: return 1; case OperandType.InlineVar: return 2; case OperandType.InlineBrTarget: case OperandType.InlineField: case OperandType.InlineI: case OperandType.InlineMethod: case OperandType.InlineSig: case OperandType.InlineString: case OperandType.InlineTok: case OperandType.InlineType: case OperandType.ShortInlineR: return 4; case OperandType.InlineI8: case OperandType.InlineR: return 8; case OperandType.InlineSwitch: RequireBytes(bytes, offset, 4); return checked(4 + ReadInt32(bytes, offset) * 4); default: throw new BadImageFormatException("unsupported operand"); } }
    private static int ReadInt32(ImmutableArray<byte> bytes, int offset)
    { RequireBytes(bytes, offset, 4); return bytes[offset] | (bytes[offset + 1] << 8) | (bytes[offset + 2] << 16) | (bytes[offset + 3] << 24); }
    private static void RequireBytes(ImmutableArray<byte> bytes, int offset, int count)
    { if (offset < 0 || count < 0 || offset > bytes.Length - count) throw new BadImageFormatException("truncated IL"); }
}

internal static class AssemblySurfaceTests
{
    internal static void Register(TestRegistry tests, HarnessOptions options)
    {
        tests.Add("assembly", "pinned Assembly-CSharp hash",
            delegate { PinnedHash(options.AssemblyPath); });
        tests.Add("assembly", "exact ten observed methods",
            delegate { ExactObservedMethods(options.AssemblyPath); });
        tests.Add("assembly", "exact required game fields",
            delegate { ExactRequiredFields(options.AssemblyPath); });
        tests.Add("assembly", "metadata matcher rejects near misses",
            SyntheticMatcherRejectsNearMisses);
        tests.Add("assembly", "replay native ABI remains exact",
            delegate { ReplayNativeAbiRemainsExact(options.AssemblyPath); });
        tests.Add("plugin", "game adapter call surface is passive",
            delegate { AdapterCallSurface(options.PluginPath); });
        tests.Add("plugin", "controller crosses authorized update boundary",
            delegate { ControllerUsesAuthorizedBoundary(options.PluginPath); });
        tests.Add("plugin", "eight Harmony patch contracts are exact",
            delegate { ExactPatchSurface(options.PluginPath); });
        tests.Add("plugin", "PE CLR and direct references are pinned",
            delegate { PluginPeAndReferences(options.PluginPath); });
        tests.Add("plugin", "BepInPlugin identity is exact",
            delegate { BepInPluginIdentity(options.PluginPath); });
        tests.Add("plugin", "typed modes and owner teardown are closed",
            delegate { TypedModeAndOwnerOnlyTeardown(options.PluginPath); });
        tests.Add("plugin", "adapter replay call surface is exact",
            delegate { AdapterReplayCallSurfaceIsExact(options.PluginPath); });
        tests.Add("plugin", "player input override is replay only",
            delegate { PlayerInputOverrideIsReplayOnly(options.PluginPath); });
    }

    private static ParameterShape P(string type) { return new ParameterShape(type); }

    private static void PinnedHash(string path)
    {
        if (String.IsNullOrEmpty(path)) throw new ArgumentException("--assembly is required");
        byte[] digest;
        using (SHA256 hash = SHA256.Create())
        using (FileStream stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read)) digest = hash.ComputeHash(stream);
        StringBuilder actual = new StringBuilder(64);
        for (int index = 0; index < digest.Length; index++) actual.Append(digest[index].ToString("x2", CultureInfo.InvariantCulture));
        Check.Equal(OracleProtocol.ExpectedAssemblySha256, actual.ToString(), "Assembly-CSharp SHA-256");
    }

    private static void ExactObservedMethods(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--assembly"))
        {
            RequireMethod(image, "Game", "Update", "private", false, "System.Void");
            RequireMethod(image, "Game", "DoPlayerInput", "private", false, "System.Void");
            RequireMethod(image, "Game", "Playerinputstring", "private", false, "Direction");
            RequireMethod(image, "GameState", "ProcessInput", "public", false, "System.Boolean", P("Direction"));
            RequireMethod(image, "Game", "DoUndo", "public", false, "System.Void");
            RequireMethod(image, "Game", "RestorePrevState", "private", false, "System.Void", P("GameState.BakStruct"));
            RequireMethod(image, "Game", "DoRestart", "public", false, "System.Void");
            RequireMethod(image, "Game", "SetGameState", "public", false, "System.Void", P("GameState"));
            RequireMethod(image, "GameState", "Moving", "public", false, "System.Boolean");
            RequireMethod(image, "GameState", "Save", "public", false, "System.String", P("System.Boolean"), P("System.Boolean"));
            Check.Equal(0, image.EnumValue("Direction", "North"), "North");
            Check.Equal(1, image.EnumValue("Direction", "South"), "South");
            Check.Equal(2, image.EnumValue("Direction", "West"), "West");
            Check.Equal(3, image.EnumValue("Direction", "East"), "East");
            Check.Equal(8, image.EnumValue("Direction", "None"), "None");
        }
    }

    private static void ExactRequiredFields(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--assembly"))
        {
            RequireField(image, "Game", "gamestate", "public", false, "GameState");
            RequireField(image, "Game", "exitSequence", "public", false, "System.Boolean");
            RequireField(image, "Game", "bluespawnanim", "public", false, "System.Boolean");
            RequireField(image, "Game", "escmenu", "public", false, "UnityEngine.GameObject");
            RequireField(image, "Game", "endingsequence", "public", true, "System.Boolean");
            RequireField(image, "Game", "leaving", "private", false, "System.Boolean");
            RequireField(image, "Game", "gameover", "private", false, "System.Boolean");
            RequireField(image, "Game", "exploding", "private", false, "System.Boolean");
            RequireField(image, "GameState", "player", "public", false, "Entity");
            RequireField(image, "GameState", "movements", "public", false, "System.Collections.Generic.List<Movement>");
            RequireField(image, "GameState", "worldsausagespawns", "public", false, "System.Collections.Generic.List<Coord>");
            RequireField(image, "GameState", "pushestotry", "public", false, "System.Int32");
            RequireField(image, "GameState", "pushtargetlevel", "public", false, "System.String");
            RequireField(image, "GameState", "overworld", "public", false, "System.Boolean");
            RequireField(image, "GameState", "won", "public", false, "System.Boolean");
            RequireField(image, "GameState", "returning", "public", false, "System.Boolean");
            RequireField(image, "GameState", "haveevercookedall", "public", false, "System.Boolean");
            RequireField(image, "GameState", "lostreason", "public", false, "System.String");
            RequireField(image, "GameState", "displayname", "public", false, "System.String");
            RequireField(image, "GameState", "sausagescooked", "public", false, "System.Int32");
            RequireField(image, "GameState", "shouldredrawcoffins", "public", true, "Coord");
            RequireField(image, "SaveGame", "homePath", "public", true, "System.String");
            RequireField(image, "SaveGame", "PersistentDataPath", "public", true, "System.String");
        }
    }

    private static void SyntheticMatcherRejectsNearMisses()
    {
        MethodShape expected = new MethodShape(default(MethodDefinitionHandle), "GameState", "ProcessInput", "public", false, "System.Boolean", new ParameterShape[] { P("Direction") });
        Check.Throws<InvalidOperationException>(delegate { RequireMethodShape(new MethodShape[] { new MethodShape(default(MethodDefinitionHandle), "GameState", "ProcessInput", "private", false, "System.Boolean", new ParameterShape[] { P("Direction") }) }, expected); }, "visibility");
        Check.Throws<InvalidOperationException>(delegate { RequireMethodShape(new MethodShape[] { new MethodShape(default(MethodDefinitionHandle), "GameState", "ProcessInput", "public", true, "System.Boolean", new ParameterShape[] { P("Direction") }) }, expected); }, "static");
        Check.Throws<InvalidOperationException>(delegate { RequireMethodShape(new MethodShape[] { new MethodShape(default(MethodDefinitionHandle), "GameState", "ProcessInput", "public", false, "System.Void", new ParameterShape[] { P("Direction") }) }, expected); }, "return");
        Check.Throws<InvalidOperationException>(delegate { RequireMethodShape(new MethodShape[] { new MethodShape(default(MethodDefinitionHandle), "GameState", "ProcessInput", "public", false, "System.Boolean", new ParameterShape[] { P("System.Int32") }) }, expected); }, "parameter");
        FieldShape field = new FieldShape("Game", "gamestate", "public", false, "GameState");
        Check.Throws<InvalidOperationException>(delegate { RequireFieldShape(new FieldShape[] { new FieldShape("Game", "gamestate", "public", false, "System.Object") }, field); }, "field type");
        Check.Throws<InvalidOperationException>(delegate { RequireEnumShape(new EnumShape[] { new EnumShape("None", 7) }, new EnumShape("None", 8)); }, "enum value");
    }

    private static void ReplayNativeAbiRemainsExact(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--assembly"))
        {
            RequireSoleMethod(image, "Game", "Playerinputstring", "private",
                false, "Direction");
            RequireSoleMethod(image, "Game", "DoPlayerInput", "private",
                false, "System.Void");
            RequireSoleMethod(image, "GameState", "ProcessInput", "public",
                false, "System.Boolean", P("Direction"));
            RequireSoleMethod(image, "Game", "DoUndo", "public", false,
                "System.Void");
            RequireSoleMethod(image, "Game", "RestorePrevState", "private",
                false, "System.Void", P("GameState.BakStruct"));
        }
    }

    private static void AdapterCallSurface(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
        {
            MethodShape[] methods = image.AllMethods("GameAdapter");
            List<MethodCall> gameCalls = new List<MethodCall>();
            MethodShape saveOwner = null;
            for (int index = 0; index < methods.Length; index++)
            {
                if (methods[index].Name == "InvokeUndo") continue;
                List<MethodCall> calls = image.Calls(methods[index]);
                for (int call = 0; call < calls.Count; call++)
                {
                    MethodCall value = calls[call];
                    if (value.Owner == "Game" || value.Owner == "GameState")
                    {
                        gameCalls.Add(value);
                        if (value.Owner == "GameState" && value.Name == "Save") saveOwner = methods[index];
                    }
                }
            }
            Check.Equal(2, gameCalls.Count, "exact direct game call count");
            RequireGameCall(gameCalls, "GameState", "Moving", "System.Boolean", new string[0]);
            RequireGameCall(gameCalls, "GameState", "Save", "System.String", new string[] { "System.Boolean", "System.Boolean" });
            if (saveOwner == null) throw new InvalidOperationException("Save owner missing");
            RequireFalseFalseBeforeSave(image, saveOwner);
        }
    }

    private static void AdapterReplayCallSurfaceIsExact(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
        {
            RequireSoleMethod(image, "IOracleGameAdapter", "InvokeUndo",
                "public", false, "System.Void", P("System.Object"));
            RequireSoleMethod(image, "GameAdapter", "InvokeUndo", "public",
                false, "System.Void", P("System.Object"));
            MethodShape[] methods = image.AllMethods("GameAdapter");
            List<MethodCall> gameCalls = new List<MethodCall>();
            for (int index = 0; index < methods.Length; index++)
            {
                List<MethodCall> calls = image.Calls(methods[index]);
                for (int call = 0; call < calls.Count; call++)
                    if (calls[call].Owner == "Game"
                        || calls[call].Owner == "GameState")
                        gameCalls.Add(calls[call]);
            }
            Check.Equal(3, gameCalls.Count,
                "exact passive-plus-replay direct game call count");
            RequireGameCall(gameCalls, "GameState", "Moving",
                "System.Boolean", new string[0]);
            RequireGameCall(gameCalls, "GameState", "Save", "System.String",
                new string[] { "System.Boolean", "System.Boolean" });
            RequireGameCall(gameCalls, "Game", "DoUndo", "System.Void",
                new string[0]);

            int directProcessInput = 0;
            string[] types = image.AllTypeNames();
            for (int type = 0; type < types.Length; type++)
            {
                MethodShape[] ownerMethods = image.AllMethods(types[type]);
                for (int method = 0; method < ownerMethods.Length; method++)
                {
                    List<MethodCall> calls = image.Calls(ownerMethods[method]);
                    for (int call = 0; call < calls.Count; call++)
                        if (calls[call].Owner == "GameState"
                            && calls[call].Name == "ProcessInput")
                            directProcessInput++;
                }
            }
            Check.Equal(0, directProcessInput,
                "plugin never directly calls GameState.ProcessInput");
        }
    }

    private static void PlayerInputOverrideIsReplayOnly(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
        {
            Check.Equal(0, image.Methods(
                "GameHooks", "AllowNativePlayerInput").Length,
                "legacy unconditional player-input gate is absent");
            MethodShape hook = RequireSoleMethod(image, "GameHooks",
                "TryOverridePlayerInput", "assembly", true, "System.Boolean",
                P("System.Int32&"));
            MethodParameterMetadata[] hookParameters =
                image.ParameterMetadata(hook);
            Check.Equal("rawDirection", hookParameters[0].Name,
                "hook raw direction parameter name");
            Check.True(hookParameters[0].IsOut,
                "hook raw direction is out");

            MethodShape prefix = RequireSoleMethod(image,
                "GamePlayerinputstringPatch", "Prefix", "private", true,
                "System.Boolean", P("Direction&"));
            MethodParameterMetadata[] prefixParameters =
                image.ParameterMetadata(prefix);
            Check.Equal("__result", prefixParameters[0].Name,
                "Harmony result parameter name");
            Check.False(prefixParameters[0].IsOut,
                "Harmony result parameter is ref");
            List<MethodCall> prefixCalls = image.Calls(prefix);
            RequireCallCount(prefixCalls, "GameHooks",
                "TryOverridePlayerInput", 1,
                "Playerinputstring prefix consults one replay gate");
            Check.Equal(1, prefixCalls.Count,
                "Playerinputstring prefix has no other call path");
            RequirePlayerInputPrefixControlFlow(image, prefix);

            List<MethodCall> hookCalls = image.Calls(hook);
            RequireCallCount(hookCalls, "GameHooks", "ReadController", 1,
                "override reads published controller once");
            RequireCallCount(hookCalls, "OracleController",
                "TryOverridePlayerInput", 1,
                "override delegates to controller once");
            RequireCallCount(hookCalls, "OracleController", "ObserverFailed", 1,
                "override exception selects observer failure once");

            MethodShape updateFinalize = RequireSoleMethod(
                image, "GameHooks", "FinalizeUpdate", "assembly", true,
                "System.Exception", P("System.Exception"));
            int updateThrewTargets = 0;
            int ordinaryFailureTargets = 0;
            List<IlInstruction> finalizeInstructions =
                image.Instructions(updateFinalize);
            for (int index = 0; index < finalizeInstructions.Count; index++)
            {
                if (finalizeInstructions[index].OpCode.Value
                    != OpCodes.Ldftn.Value) continue;
                MethodCall target = image.MethodTokenCall(
                    finalizeInstructions[index]);
                if (target.Owner == "OracleController"
                    && target.Name == "UpdateThrew") updateThrewTargets++;
                if (target.Owner == "OracleController"
                    && target.Name == "GameMethodFailed") ordinaryFailureTargets++;
            }
            Check.Equal(1, updateThrewTargets,
                "Update finalizer uses replay-aware failure action");
            Check.Equal(0, ordinaryFailureTargets,
                "Update finalizer bypasses ordinary game failure action");
        }
    }

    private static void ControllerUsesAuthorizedBoundary(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
        {
            List<MethodCall> observe = image.Calls(OnlyMethod(
                image, "OracleController", "ObserveUpdate"));
            RequireOrderedCalls(observe, new string[]
            {
                "OracleController.AdapterUpdateObservation::.ctor",
                "PassiveUpdateBoundary::Observe"
            }, "controller update boundary");

            List<MethodCall> boundary = image.Calls(OnlyMethod(
                image, "PassiveUpdateBoundary", "Observe"));
            RequireOrderedCalls(boundary, new string[]
            {
                "IPassiveUpdateObservation::TryGetState",
                "IPassiveUpdateObservation::NowSeconds",
                "IPassiveUpdateObservation::VerifySavePath",
                "IPassiveUpdateObservation::TryGetState",
                "IPassiveUpdateObservation::IsQuiescent",
                "IPassiveUpdateObservation::Capture",
                "IPassiveUpdateObservation::UtcNow"
            }, "state/clock/path/state/gate/capture/utc order");

            MethodShape[] methods = image.AllMethods("OracleController");
            List<string> movementOwners = new List<string>();
            for (int method = 0; method < methods.Length; method++)
            {
                List<MethodCall> calls = image.Calls(methods[method]);
                for (int call = 0; call < calls.Count; call++)
                    if (calls[call].Owner == "IOracleGameAdapter"
                        && (calls[call].Name == "MovementScheduled"
                            || calls[call].Name == "CurrentMovementScheduled"))
                        movementOwners.Add(methods[method].Name + "::" + calls[call].Name);
            }
            movementOwners.Sort(StringComparer.Ordinal);
            RequireSequence(new string[]
            {
                "ProcessInputReturned::MovementScheduled",
                "UndoReturned::CurrentMovementScheduled"
            }, movementOwners.ToArray(), "movement reads stay on normal returns");
            RequireReplayControllerRouting(image);
        }
    }

    private static void ExactPatchSurface(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
        {
            string[] patches = new string[]
            {
                "GameUpdatePatch", "GameDoPlayerInputPatch",
                "GamePlayerinputstringPatch", "GameStateProcessInputPatch",
                "GameDoUndoPatch", "GameRestorePrevStatePatch",
                "GameDoRestartPatch", "GameSetGameStatePatch"
            };
            List<string> attributed = new List<string>();
            string[] allTypes = image.AllTypeNames();
            for (int index = 0; index < allTypes.Length; index++)
                if (image.HasTypeAttribute(allTypes[index], "HarmonyLib.HarmonyPatch"))
                    attributed.Add(allTypes[index]);
            attributed.Sort(StringComparer.Ordinal);
            string[] expectedPatches = (string[])patches.Clone();
            Array.Sort(expectedPatches, StringComparer.Ordinal);
            RequireSequence(expectedPatches, attributed.ToArray(),
                "exact HarmonyPatch types");

            RequirePatch(image, "GameUpdatePatch", new string[][]
            {
                S("Prefix", "System.Void", "Game"),
                S("Postfix", "System.Void", "Game"),
                S("Finalizer", "System.Exception", "System.Exception")
            });
            RequirePatch(image, "GameDoPlayerInputPatch", new string[][]
            {
                S("Prefix", "System.Void", "HookToken&"),
                S("Postfix", "System.Void", "HookToken"),
                S("Finalizer", "System.Exception", "System.Exception", "HookToken")
            });
            RequirePatch(image, "GamePlayerinputstringPatch", new string[][]
            {
                S("Prefix", "System.Boolean", "Direction&"),
                S("Postfix", "System.Void", "Direction")
            });
            RequirePatch(image, "GameStateProcessInputPatch", new string[][]
            {
                S("Prefix", "System.Void", "GameState", "Direction", "HookToken&"),
                S("Postfix", "System.Void", "GameState", "System.Boolean", "HookToken"),
                S("Finalizer", "System.Exception", "System.Exception", "HookToken")
            });
            RequirePatch(image, "GameDoUndoPatch", new string[][]
            {
                S("Prefix", "System.Void", "Game", "HookToken&"),
                S("Postfix", "System.Void", "Game", "HookToken"),
                S("Finalizer", "System.Exception", "System.Exception", "HookToken")
            });
            RequirePatch(image, "GameRestorePrevStatePatch", new string[][]
            { S("Prefix", "System.Void", "GameState.BakStruct") });
            RequirePatch(image, "GameDoRestartPatch", new string[][]
            {
                S("Prefix", "System.Void", "HookToken&"),
                S("Postfix", "System.Void", "HookToken"),
                S("Finalizer", "System.Exception", "System.Exception", "HookToken")
            });
            RequirePatch(image, "GameSetGameStatePatch", new string[][]
            {
                S("Prefix", "System.Void", "Game", "GameState", "HookToken&"),
                S("Postfix", "System.Void", "Game", "HookToken"),
                S("Finalizer", "System.Exception", "System.Exception", "HookToken")
            });

            RequireTargetMethod(image, "GameUpdatePatch", "Game", "Update",
                (int)(BindingFlags.Instance | BindingFlags.NonPublic),
                "System.Void");
            RequireTargetMethod(image, "GameDoPlayerInputPatch", "Game",
                "DoPlayerInput",
                (int)(BindingFlags.Instance | BindingFlags.NonPublic),
                "System.Void");
            RequireTargetMethod(image, "GamePlayerinputstringPatch", "Game",
                "Playerinputstring",
                (int)(BindingFlags.Instance | BindingFlags.NonPublic),
                "Direction");
            RequireTargetMethod(image, "GameStateProcessInputPatch", "GameState",
                "ProcessInput", (int)(BindingFlags.Instance | BindingFlags.Public),
                "System.Boolean", "Direction");
            RequireTargetMethod(image, "GameDoUndoPatch", "Game", "DoUndo",
                (int)(BindingFlags.Instance | BindingFlags.Public), "System.Void");
            RequireTargetMethod(image, "GameRestorePrevStatePatch", "Game",
                "RestorePrevState",
                (int)(BindingFlags.Instance | BindingFlags.NonPublic),
                "System.Void", "GameState.BakStruct");
            RequireTargetMethod(image, "GameDoRestartPatch", "Game", "DoRestart",
                (int)(BindingFlags.Instance | BindingFlags.Public), "System.Void");
            RequireTargetMethod(image, "GameSetGameStatePatch", "Game",
                "SetGameState", (int)(BindingFlags.Instance | BindingFlags.Public),
                "System.Void", "GameState");

            RequireObservedForwarding(image, "GameUpdatePatch", "Prefix",
                "UpdateEntered", new string[] { "System.Object" },
                new string[] { "__instance" });
            RequireObservedForwarding(image, "GameUpdatePatch", "Postfix",
                "ObserveUpdate", new string[] { "System.Object" },
                new string[] { "__instance" });
            RequireObservedForwarding(image, "GameDoPlayerInputPatch", "Prefix",
                "PlayerPollEntered", new string[0], new string[0]);
            RequireObservedForwarding(image, "GameDoPlayerInputPatch", "Postfix",
                "PlayerPollReturned", new string[] { "HookToken" },
                new string[] { "__state" });
            RequireObservedForwarding(image, "GamePlayerinputstringPatch", "Postfix",
                "PhysicalPollReturned", new string[] { "System.Int32" },
                new string[] { "__result" });
            RequireObservedForwarding(image, "GameStateProcessInputPatch", "Prefix",
                "ProcessInputEntered",
                new string[] { "System.Object", "System.Int32" },
                new string[] { "__instance", "__0" });
            RequireObservedForwarding(image, "GameStateProcessInputPatch", "Postfix",
                "ProcessInputReturned",
                new string[] { "HookToken", "System.Boolean", "System.Object" },
                new string[] { "__state", "__result", "__instance" });
            RequireObservedForwarding(image, "GameDoUndoPatch", "Prefix",
                "UndoEntered", new string[] { "System.Object" },
                new string[] { "__instance" });
            RequireObservedForwarding(image, "GameDoUndoPatch", "Postfix",
                "UndoReturned", new string[] { "HookToken", "System.Object" },
                new string[] { "__state", "__instance" });
            RequireObservedForwarding(image, "GameRestorePrevStatePatch", "Prefix",
                "RestoreObserved", new string[0], new string[0]);
            RequireObservedForwarding(image, "GameDoRestartPatch", "Prefix",
                "RestartEntered", new string[0], new string[0]);
            RequireObservedForwarding(image, "GameDoRestartPatch", "Postfix",
                "RestartReturned", new string[] { "HookToken" },
                new string[] { "__state" });
            RequireObservedForwarding(image, "GameSetGameStatePatch", "Prefix",
                "StateSetEntered", new string[] { "System.Object", "System.Object" },
                new string[] { "__instance", "__0" });
            RequireObservedForwarding(image, "GameSetGameStatePatch", "Postfix",
                "StateSetReturned", new string[] { "HookToken", "System.Object" },
                new string[] { "__state", "__instance" });

            RequireTokenStateWriteBack(image, "GameDoPlayerInputPatch",
                "PlayerPollEntered", 0);
            RequireTokenStateWriteBack(image, "GameStateProcessInputPatch",
                "ProcessInputEntered", 2);
            RequireTokenStateWriteBack(image, "GameDoUndoPatch",
                "UndoEntered", 1);
            RequireTokenStateWriteBack(image, "GameDoRestartPatch",
                "RestartEntered", 0);
            RequireTokenStateWriteBack(image, "GameSetGameStatePatch",
                "StateSetEntered", 2);
            RequireInertBeforeObserve(image, "GameDoPlayerInputPatch", 0);
            RequireInertBeforeObserve(image, "GameStateProcessInputPatch", 1);
            RequireInertBeforeObserve(image, "GameDoUndoPatch", 2);
            RequireInertBeforeObserve(image, "GameDoRestartPatch", 3);
            RequireInertBeforeObserve(image, "GameSetGameStatePatch", 4);

            RequireDirectReturnCall(image, "GameUpdatePatch", "Finalizer",
                "GameHooks", "FinalizeUpdate", new int[] { 0 });
            string[] tokenFinalizers = new string[]
            {
                "GameDoPlayerInputPatch", "GameStateProcessInputPatch",
                "GameDoUndoPatch", "GameDoRestartPatch", "GameSetGameStatePatch"
            };
            for (int index = 0; index < tokenFinalizers.Length; index++)
                RequireDirectReturnCall(image, tokenFinalizers[index], "Finalizer",
                    "GameHooks", "Finalize", new int[] { 1, 0 });

            for (int patch = 0; patch < patches.Length; patch++)
            {
                MethodShape[] methods = image.AllMethods(patches[patch]);
                for (int method = 0; method < methods.Length; method++)
                {
                    MethodParameterMetadata[] parameters =
                        image.ParameterMetadata(methods[method]);
                    for (int parameter = 0; parameter < parameters.Length; parameter++)
                    {
                        bool byReference = methods[method].Parameters[parameter]
                            .Type.EndsWith("&", StringComparison.Ordinal);
                        if (byReference)
                        {
                            bool playerResult = patches[patch]
                                    == "GamePlayerinputstringPatch"
                                && methods[method].Name == "Prefix"
                                && parameters[parameter].Name == "__result";
                            if (playerResult)
                                Check.False(parameters[parameter].IsOut,
                                    "Playerinputstring __result is ref");
                            else
                            {
                                Check.Equal("__state", parameters[parameter].Name,
                                    "only __state or player __result is by-ref");
                                Check.True(parameters[parameter].IsOut,
                                    "by-ref __state is out");
                            }
                        }
                    }
                }
            }
        }
    }

    private static void PluginPeAndReferences(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
        {
            Check.Equal(PEMagic.PE32, image.Headers.PEHeader.Magic, "PE32");
            CorFlags flags = image.Headers.CorHeader.Flags;
            Check.True((flags & CorFlags.ILOnly) != 0, "IL-only");
            Check.True((flags & (CorFlags.Requires32Bit | CorFlags.Prefers32Bit)) == 0,
                "AnyCPU");
            Check.Equal("v2.0.50727", image.Reader.MetadataVersion, "CLR metadata");
            string[] allowed = new string[]
            {
                "0Harmony", "Assembly-CSharp", "BepInEx", "System",
                "System.Core", "UnityEngine.CoreModule", "mscorlib"
            };
            string[] references = image.AssemblyReferences();
            for (int index = 0; index < references.Length; index++)
                Check.True(Array.IndexOf(allowed, references[index]) >= 0,
                    "unexpected direct reference: " + references[index]);
            Check.True(Array.IndexOf(references, "0Harmony") >= 0, "Harmony reference");
            Check.True(Array.IndexOf(references, "Assembly-CSharp") >= 0,
                "game reference");
            Check.True(Array.IndexOf(references, "BepInEx") >= 0, "BepInEx reference");
            Check.False(File.Exists(Path.ChangeExtension(path, ".pdb")), "no Release PDB");
            string directory = Path.GetDirectoryName(path);
            string[] external = new string[]
            { "0Harmony.dll", "Assembly-CSharp.dll", "BepInEx.dll", "UnityEngine.dll", "UnityEngine.CoreModule.dll" };
            for (int index = 0; index < external.Length; index++)
                Check.False(File.Exists(Path.Combine(directory, external[index])),
                    "non-copying reference: " + external[index]);
        }
    }

    private static void BepInPluginIdentity(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
            RequireSequence(new string[]
            {
                "dev.jlsor.ssr.oracle", "SSR Executable Oracle", "0.3.0"
            }, image.TypeAttributeStrings(
                "SsrOracle.Plugin", "BepInEx.BepInPlugin"),
                "BepInPlugin identity");
    }

    private static void TypedModeAndOwnerOnlyTeardown(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
        {
            Check.Equal(0, image.EnumValue("OracleMode", "Off"), "Off mode");
            Check.Equal(1, image.EnumValue("OracleMode", "Passive"), "Passive mode");
            Check.Equal(2, image.EnumValue("OracleMode", "Replay"), "Replay mode");
            string[] allowedReplayTypes = new string[]
            {
                "IReplayDriver", "IReplayInputBytes", "ReplayInput",
                "FileReplayInputBytes", "ReplayConfiguration",
                "IReplayUpdateAccess", "ReplayCoordinator",
                "OracleController.AdapterReplayUpdateAccess"
            };
            string[] types = image.AllTypeNames();
            for (int index = 0; index < types.Length; index++)
            {
                if (types[index].IndexOf("Replay", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    Check.True(Array.IndexOf(allowedReplayTypes, types[index]) >= 0,
                        "only planned replay types are present: " + types[index]);
                }
            }
            Check.Equal("dev.jlsor.ssr.oracle.passive",
                image.StringConstant("GameHooks", "HarmonyOwner"), "passive owner");

            MethodShape awakeMethod = OnlyMethod(image, "SsrOracle.Plugin", "Awake");
            List<MethodCall> awake = image.Calls(awakeMethod);
            RequireCallCount(awake, "OracleConfiguration", "Load", 1, "config loaded once");
            RequireCallCount(awake, "PluginModePolicy", "StartOff", 1,
                "Off uses legacy policy");
            RequireCallCount(awake, "OracleController", "Start", 2,
                "both active modes start one controller branch");
            RequireAwakeModeControlFlow(image, awakeMethod, awake);

            List<MethodCall> destroy = image.Calls(
                OnlyMethod(image, "SsrOracle.Plugin", "OnDestroy"));
            RequireCallCount(destroy, "OracleController", "Dispose", 1,
                "OnDestroy delegates once");
            for (int index = 0; index < destroy.Count; index++)
                Check.False(destroy[index].Name == "UnpatchSelf"
                    || destroy[index].Name == "Close",
                    "OnDestroy has no direct teardown");
            RequireSoleControllerDispose(image);

            List<MethodCall> unpatch = image.Calls(
                OnlyMethod(image, "SsrOracle.Plugin.OracleRuntimeHost", "UnpatchSelf"));
            RequireOrderedCalls(unpatch, new string[]
            { "HarmonyLib.Harmony::UnpatchSelf", "GameHooks::Clear" },
                "owner-only unpatch before clear");
        }
    }

    private static void RequireAwakeModeControlFlow(MetadataImage image,
        MethodShape awakeMethod, List<MethodCall> calls)
    {
        List<IlInstruction> instructions = image.Instructions(awakeMethod);
        MethodCall load = OnlyCall(calls, "OracleConfiguration", "Load",
            "Awake config load");
        List<MethodCall> modeCalls = CallsNamed(
            calls, "OracleConfiguration", "get_Mode");
        Check.Equal(5, modeCalls.Count, "Awake exact typed mode gates");
        MethodCall startOff = OnlyCall(calls, "PluginModePolicy", "StartOff",
            "Awake Off policy");
        Check.True(load.Offset < modeCalls[0].Offset,
            "configuration load precedes Off gate");
        Check.True(modeCalls[0].Offset < startOff.Offset,
            "Off policy follows the Off gate");

        int offBranchIndex = FindConditionalBranch(
            instructions, modeCalls[0].Offset, startOff.Offset,
            "Off mode branch");
        IlInstruction offBranch = instructions[offBranchIndex];
        Check.True(IsBranchOnTrue(offBranch),
            "non-Off value branches around the Off region");
        int startOffIndex = InstructionIndex(instructions, startOff.Offset);
        Check.True(startOffIndex + 1 < instructions.Count
            && instructions[startOffIndex + 1].OpCode.Value
                == OpCodes.Ret.Value,
            "Off StartOff region returns immediately");
        Check.True(offBranch.BranchTarget
                > instructions[startOffIndex + 1].Offset
            && offBranch.BranchTarget <= modeCalls[1].Offset,
            "non-Off target cannot enter or fall through the Off region");

        int passiveValidBranch = RequireModeComparison(
            instructions, modeCalls[1], 1, "Passive validity gate");
        int replayValidBranch = RequireModeComparison(
            instructions, modeCalls[2], 2, "Replay validity gate");
        Check.True(IsBranchOnEqual(instructions[passiveValidBranch])
            && IsBranchOnEqual(instructions[replayValidBranch]),
            "Passive and Replay values branch around invalid reporting");
        Check.Equal(instructions[passiveValidBranch].BranchTarget,
            instructions[replayValidBranch].BranchTarget,
            "both active modes enter one shared capability region");
        int invalidString = OnlyStringInstruction(
            image, instructions, "invalid_mode", "invalid mode marker");
        int invalidFailed = FirstCallInstructionAfter(
            instructions, invalidString, "invalid mode reporter");
        MethodCall invalidCall = image.MethodTokenCall(
            instructions[invalidFailed]);
        Check.True(invalidCall.Owner == "PassiveLogReporter"
                && invalidCall.Name == "Failed",
            "invalid mode selects the bootstrap reporter");
        Check.True(invalidFailed + 1 < instructions.Count
            && instructions[invalidFailed + 1].OpCode.Value
                == OpCodes.Ret.Value,
            "invalid mode returns before active capabilities");
        int activeTarget = instructions[passiveValidBranch].BranchTarget;
        Check.True(activeTarget > instructions[invalidFailed + 1].Offset
            && activeTarget <= modeCalls[3].Offset,
            "active mode branches skip the complete invalid return region");
        RequireActiveReporterSelection(image, instructions, calls,
            modeCalls[3], activeTarget);

        MethodCall validate = OnlyCall(calls,
            "SsrOracle.Plugin.OracleRuntimeHost",
            "ValidateAssemblyAndPassiveContract",
            "replay pre-input runtime validation");
        MethodCall inputLoad = OnlyCall(calls, "ReplayInput", "Load",
            "replay exact input read");
        Check.True(validate.Offset < inputLoad.Offset,
            "runtime contract validates before replay input read");

        List<MethodCall> constructors = CallsNamed(
            calls, "OracleController", ".ctor");
        Check.Equal(2, constructors.Count,
            "one Passive and one Replay controller constructor branch");
        MethodCall passiveConstructor = null;
        MethodCall replayConstructor = null;
        for (int index = 0; index < constructors.Count; index++)
        {
            MethodCall value = constructors[index];
            if (value.Parameters.Length == 4
                && value.Parameters[0] == "PassiveConfiguration")
                passiveConstructor = value;
            if (value.Parameters.Length == 5
                && value.Parameters[0] == "ReplayConfiguration"
                && value.Parameters[1] == "ReplayInput")
                replayConstructor = value;
        }
        Check.True(passiveConstructor != null,
            "Passive controller constructor is exact");
        Check.True(replayConstructor != null,
            "Replay controller constructor is exact");
        Check.True(inputLoad.Offset < replayConstructor.Offset,
            "input is loaded before Replay controller construction");
        MethodCall harmonyConstructor = OnlyCall(calls,
            "HarmonyLib.Harmony", ".ctor", "one active Harmony constructor");
        MethodCall adapterConstructor = OnlyCall(calls,
            "GameAdapter", ".ctor", "one active adapter constructor");
        MethodCall runtimeConstructor = OnlyCall(calls,
            "SsrOracle.Plugin.OracleRuntimeHost", ".ctor",
            "one active runtime constructor");
        Check.True(activeTarget <= harmonyConstructor.Offset
            && activeTarget <= adapterConstructor.Offset
            && activeTarget <= runtimeConstructor.Offset
            && activeTarget <= passiveConstructor.Offset
            && activeTarget <= replayConstructor.Offset,
            "invalid modes cannot reach active capability construction");

        MethodCall executionMode = modeCalls[4];
        Check.True(executionMode.Offset < validate.Offset,
            "Replay execution gate precedes Replay-only validation");
        int executionBranch = RequireModeComparison(
            instructions, executionMode, 2, "Replay execution gate");
        Check.True(IsBranchOnNotEqual(instructions[executionBranch]),
            "Replay equality routes every non-Replay mode to Passive");
        int passiveTarget = instructions[executionBranch].BranchTarget;

        List<MethodCall> starts = CallsNamed(
            calls, "OracleController", "Start");
        Check.Equal(2, starts.Count, "two exclusive active Start call sites");
        List<MethodCall> runConstructors = CallsNamed(
            calls, "RunRecord", ".ctor");
        Check.Equal(2, runConstructors.Count,
            "one Passive and one Replay Run constructor branch");
        MethodCall passiveRun = null;
        MethodCall replayRun = null;
        for (int index = 0; index < runConstructors.Count; index++)
        {
            MethodCall value = runConstructors[index];
            if (value.Parameters.Length == 3)
                passiveRun = value;
            if (value.Parameters.Length == 6
                && value.Parameters[1] == "OracleMode")
                replayRun = value;
        }
        Check.True(passiveRun != null, "Passive Run constructor is exact");
        Check.True(replayRun != null, "Replay Run constructor is exact");

        Check.True(instructions[executionBranch].Offset < validate.Offset
            && validate.Offset < inputLoad.Offset
            && inputLoad.Offset < replayConstructor.Offset
            && replayConstructor.Offset < replayRun.Offset
            && replayRun.Offset < starts[0].Offset
            && starts[0].Offset < passiveTarget,
            "Replay branch exclusively validates loads constructs runs and starts");
        Check.True(passiveTarget <= passiveConstructor.Offset
            && passiveConstructor.Offset < passiveRun.Offset
            && passiveRun.Offset < starts[1].Offset,
            "Passive branch exclusively constructs runs and starts without input");
        RequireMutuallyExclusiveActiveExits(
            instructions, starts[0], starts[1]);
        RequireCallCount(calls, "NdjsonTraceSink", "Create", 0,
            "Awake opens no sink directly");
        RequireCallCount(calls, "GameAdapter",
            "AuthenticateAndRedirectSavePath", 0,
            "Awake redirects no save path directly");
    }

    private static void RequireActiveReporterSelection(MetadataImage image,
        List<IlInstruction> instructions, List<MethodCall> calls,
        MethodCall modeCall, int activeTarget)
    {
        int reporterBranch = RequireModeComparison(
            instructions, modeCall, 2, "active reporter Replay gate");
        Check.True(IsBranchOnEqual(instructions[reporterBranch]),
            "Replay alone selects the provisional Replay reporter");

        List<MethodCall> reporterConstructors = CallsNamed(
            calls, "PassiveLogReporter", ".ctor");
        Check.Equal(2, reporterConstructors.Count,
            "bootstrap and provisional reporter constructors only");
        MethodCall bootstrap = null;
        MethodCall provisional = null;
        for (int index = 0; index < reporterConstructors.Count; index++)
        {
            MethodCall value = reporterConstructors[index];
            if (value.Parameters.Length == 1
                && value.Parameters[0] == "IPassiveLog")
                bootstrap = value;
            if (value.Parameters.Length == 3
                && value.Parameters[0] == "IPassiveLog"
                && value.Parameters[1] == "OracleMode"
                && value.Parameters[2] == "System.Int32")
                provisional = value;
        }
        Check.True(bootstrap != null,
            "bootstrap Passive reporter constructor is exact");
        Check.True(provisional != null,
            "provisional Replay reporter constructor is exact");
        Check.True(bootstrap.Offset < activeTarget
            && instructions[reporterBranch].Offset
                < instructions[reporterBranch].BranchTarget
            && instructions[reporterBranch].BranchTarget
                < provisional.Offset,
            "Replay reporter construction lies only on the Replay edge");

        int bootstrapIndex = InstructionIndex(instructions, bootstrap.Offset);
        int logFieldToken = -1;
        int bootstrapLocal = -1;
        Check.True(bootstrapIndex > 0
            && instructions[bootstrapIndex - 1].OpCode.Value
                == OpCodes.Ldfld.Value
            && image.FieldName(instructions[bootstrapIndex - 1]) == "log"
            && (logFieldToken = instructions[bootstrapIndex - 1].Token) != 0
            && bootstrapIndex + 1 < instructions.Count
            && TryLocalStoreIndex(
                instructions[bootstrapIndex + 1], out bootstrapLocal),
            "bootstrap reporter stores one exact log-backed local");

        int provisionalIndex = InstructionIndex(
            instructions, provisional.Offset);
        int provisionalMode = -1;
        int provisionalCount = -1;
        Check.True(provisionalIndex >= 4
            && IsLocalLoad(instructions[provisionalIndex - 4].OpCode)
            && instructions[provisionalIndex - 3].OpCode.Value
                == OpCodes.Ldfld.Value
            && instructions[provisionalIndex - 3].Token == logFieldToken
            && MetadataImage.TryConstant(
                instructions[provisionalIndex - 2], out provisionalMode)
            && provisionalMode == 2
            && MetadataImage.TryConstant(
                instructions[provisionalIndex - 1], out provisionalCount)
            && provisionalCount == 1,
            "Replay edge constructs PassiveLogReporter(log, Replay, 1)");

        int replaySelection = InstructionIndex(instructions,
            instructions[reporterBranch].BranchTarget);
        Check.Equal(provisionalIndex - 4, replaySelection,
            "Replay branch target begins exact provisional constructor arguments");
        int passiveSelection = NextNonNop(
            instructions, reporterBranch + 1);
        int selectedBootstrap = -1;
        Check.True(TryLocalLoadIndex(
                instructions[passiveSelection], out selectedBootstrap)
            && selectedBootstrap == bootstrapLocal,
            "Passive edge selects the existing bootstrap reporter");
        int passiveJoinBranch = NextNonNop(
            instructions, passiveSelection + 1);
        Check.True(IsUnconditionalBranchOrLeave(
                instructions[passiveJoinBranch]),
            "Passive reporter selection branches to one join");
        int passiveJoin = InstructionIndex(instructions,
            instructions[passiveJoinBranch].BranchTarget);
        int replayJoin = NextNonNop(instructions, provisionalIndex + 1);
        Check.Equal(replayJoin, passiveJoin,
            "Replay and Passive reporter edges share one exact join");
        int activeReporterLocal = -1;
        Check.True(TryLocalStoreIndex(
                instructions[replayJoin], out activeReporterLocal),
            "reporter selection join stores one active reporter local");
        RequireReporterFailureUsesSelectedLocal(
            image, instructions, calls, replayJoin, activeReporterLocal);
    }

    private static void RequireReporterFailureUsesSelectedLocal(
        MetadataImage image, List<IlInstruction> instructions,
        List<MethodCall> calls, int joinIndex, int activeReporterLocal)
    {
        int priorReporterCall = joinIndex;
        int failedUses = 0;
        int diagnosticUses = 0;
        for (int index = 0; index < calls.Count; index++)
        {
            MethodCall call = calls[index];
            if (call.Offset <= instructions[joinIndex].Offset
                || call.Owner != "PassiveLogReporter"
                || (call.Name != "Failed" && call.Name != "Diagnostic"))
                continue;
            int callIndex = InstructionIndex(instructions, call.Offset);
            bool selected = false;
            for (int instruction = priorReporterCall + 1;
                instruction < callIndex; instruction++)
            {
                int loaded = -1;
                if (TryLocalLoadIndex(
                        instructions[instruction], out loaded)
                    && loaded == activeReporterLocal)
                    selected = true;
            }
            Check.True(selected,
                "startup failure handlers use the selected reporter local");
            if (call.Name == "Failed") failedUses++;
            else diagnosticUses++;
            priorReporterCall = callIndex;
        }
        Check.Equal(3, failedUses,
            "three startup failure markers use selected reporter");
        Check.Equal(3, diagnosticUses,
            "three startup diagnostics use selected reporter");
    }

    private static void RequireMutuallyExclusiveActiveExits(
        List<IlInstruction> instructions, MethodCall replayStart,
        MethodCall passiveStart)
    {
        int replayStartIndex = InstructionIndex(
            instructions, replayStart.Offset);
        int passiveStartIndex = InstructionIndex(
            instructions, passiveStart.Offset);
        int replayPop = NextNonNop(instructions, replayStartIndex + 1);
        int passivePop = NextNonNop(instructions, passiveStartIndex + 1);
        Check.True(instructions[replayPop].OpCode.Value == OpCodes.Pop.Value
            && instructions[passivePop].OpCode.Value == OpCodes.Pop.Value,
            "both active Start results are discarded before branch exit");
        int replayExit = NextNonNop(instructions, replayPop + 1);
        int passiveExit = NextNonNop(instructions, passivePop + 1);
        Check.True(IsUnconditionalBranchOrLeave(instructions[replayExit]),
            "Replay Start exits unconditionally before Passive construction");
        Check.True(IsUnconditionalBranchOrLeave(instructions[passiveExit]),
            "Passive Start exits its complete active region");
        Check.Equal(instructions[passiveExit].Offset,
            instructions[replayExit].BranchTarget,
            "Replay exits at the Passive region's unconditional exit boundary");
        Check.True(instructions[replayExit].BranchTarget
                > instructions[passivePop].Offset
            && instructions[passiveExit].BranchTarget
                > instructions[passiveExit].Offset,
            "Replay exit target lies strictly beyond the complete Passive calls");
        InstructionIndex(instructions,
            instructions[replayExit].BranchTarget);
    }

    private static int NextNonNop(
        List<IlInstruction> instructions, int start)
    {
        int index = start;
        while (index < instructions.Count
            && instructions[index].OpCode.Value == OpCodes.Nop.Value)
            index++;
        Check.True(index < instructions.Count,
            "control-flow successor instruction exists");
        return index;
    }

    private static bool IsUnconditionalBranchOrLeave(
        IlInstruction instruction)
    {
        short opcode = instruction.OpCode.Value;
        return instruction.HasBranchTarget
            && (opcode == OpCodes.Br.Value
                || opcode == OpCodes.Br_S.Value
                || opcode == OpCodes.Leave.Value
                || opcode == OpCodes.Leave_S.Value);
    }

    private static int RequireModeComparison(
        List<IlInstruction> instructions, MethodCall modeCall,
        int expectedMode, string message)
    {
        int callIndex = InstructionIndex(instructions, modeCall.Offset);
        int actualMode = -1;
        Check.True(callIndex + 2 < instructions.Count
            && MetadataImage.TryConstant(
                instructions[callIndex + 1], out actualMode)
            && actualMode == expectedMode
            && instructions[callIndex + 2].HasBranchTarget
            && instructions[callIndex + 2].OpCode.FlowControl
                == FlowControl.Cond_Branch,
            message + " compares the exact enum value then branches");
        return callIndex + 2;
    }

    private static bool IsBranchOnTrue(IlInstruction instruction)
    {
        return instruction.OpCode.Value == OpCodes.Brtrue.Value
            || instruction.OpCode.Value == OpCodes.Brtrue_S.Value;
    }

    private static bool IsBranchOnEqual(IlInstruction instruction)
    {
        return instruction.OpCode.Value == OpCodes.Beq.Value
            || instruction.OpCode.Value == OpCodes.Beq_S.Value;
    }

    private static bool IsBranchOnNotEqual(IlInstruction instruction)
    {
        return instruction.OpCode.Value == OpCodes.Bne_Un.Value
            || instruction.OpCode.Value == OpCodes.Bne_Un_S.Value;
    }

    private static int OnlyStringInstruction(MetadataImage image,
        List<IlInstruction> instructions, string value, string message)
    {
        int found = -1;
        for (int index = 0; index < instructions.Count; index++)
        {
            if (instructions[index].OpCode.Value != OpCodes.Ldstr.Value
                || image.StringLiteral(instructions[index]) != value)
                continue;
            Check.Equal(-1, found, message + " is unique");
            found = index;
        }
        if (found < 0)
            throw new InvalidOperationException(message + " is missing");
        return found;
    }

    private static int FirstCallInstructionAfter(
        List<IlInstruction> instructions, int afterIndex, string message)
    {
        for (int index = afterIndex + 1; index < instructions.Count; index++)
        {
            short opcode = instructions[index].OpCode.Value;
            if (opcode == OpCodes.Call.Value
                || opcode == OpCodes.Callvirt.Value
                || opcode == OpCodes.Newobj.Value)
                return index;
            if (instructions[index].HasBranchTarget
                || opcode == OpCodes.Ret.Value)
                break;
        }
        throw new InvalidOperationException(message + " is missing");
    }

    private static void RequireSoleControllerDispose(MetadataImage image)
    {
        int count = 0;
        string owner = null;
        string[] types = image.AllTypeNames();
        for (int type = 0; type < types.Length; type++)
        {
            MethodShape[] methods = image.AllMethods(types[type]);
            for (int method = 0; method < methods.Length; method++)
            {
                List<MethodCall> calls = image.Calls(methods[method]);
                for (int call = 0; call < calls.Count; call++)
                {
                    if (calls[call].Owner != "OracleController"
                        || calls[call].Name != "Dispose") continue;
                    count++;
                    owner = methods[method].Owner + "::" + methods[method].Name;
                }
            }
        }
        Check.Equal(1, count, "sole controller Dispose call");
        Check.Equal("SsrOracle.Plugin::OnDestroy", owner,
            "OnDestroy owns controller disposal");
    }

    private static void RequirePostGateCall(List<MethodCall> calls,
        string owner, string name, int passiveTarget, string message)
    {
        MethodCall call = OnlyCall(calls, owner, name, message);
        Check.True(call.Offset >= passiveTarget, message + " lies after gate");
    }

    private static void RequireClosedPreGateRegion(MetadataImage image,
        MethodShape awakeMethod, List<IlInstruction> instructions,
        int passiveTarget)
    {
        for (int index = 0; index < instructions.Count; index++)
        {
            IlInstruction instruction = instructions[index];
            if (instruction.Offset >= passiveTarget) continue;
            short opcode = instruction.OpCode.Value;
            if (opcode == OpCodes.Call.Value
                || opcode == OpCodes.Callvirt.Value
                || opcode == OpCodes.Newobj.Value)
            {
                MethodCall call = image.MethodTokenCall(instruction);
                Check.True(IsAllowedPreGateCall(call),
                    "unexpected pre-Passive call: "
                    + call.Owner + "::" + call.Name);
                continue;
            }
            if (opcode == OpCodes.Ldfld.Value || opcode == OpCodes.Stfld.Value
                || opcode == OpCodes.Ldsfld.Value || opcode == OpCodes.Stsfld.Value)
            {
                string field = image.FieldName(instruction);
                Check.True(field == "log"
                    || field.StartsWith("<>9__", StringComparison.Ordinal),
                    "unexpected pre-Passive field access: " + field);
                continue;
            }
            if (opcode == OpCodes.Ldstr.Value)
            {
                string value = image.StringLiteral(instruction);
                Check.True(value == "dev.jlsor.ssr.oracle.cfg"
                    || value == "invalid_mode",
                    "unexpected pre-Passive string: " + value);
                continue;
            }
            if (opcode == OpCodes.Ldftn.Value)
            {
                MethodCall target = image.MethodTokenCall(instruction);
                bool legacy = target.Owner == "GameContract"
                    && target.Name == "ValidateLegacySurface";
                bool boot = target.Owner.StartsWith(
                        "SsrOracle.Plugin.", StringComparison.Ordinal)
                    && target.Name.IndexOf(
                        "<Awake>", StringComparison.Ordinal) >= 0;
                Check.True(legacy || boot,
                    "unexpected pre-Passive delegate: "
                    + target.Owner + "::" + target.Name);
                continue;
            }
            if (instruction.HasBranchTarget)
            {
                Check.True(instruction.BranchTarget <= passiveTarget
                    || IsReturnOffset(instructions, instruction.BranchTarget),
                    "pre-Passive branch escapes closed region: "
                    + instruction.OpCode.Name + " at "
                    + instruction.Offset.ToString(CultureInfo.InvariantCulture)
                    + " -> " + instruction.BranchTarget.ToString(
                        CultureInfo.InvariantCulture) + ", gate "
                    + passiveTarget.ToString(CultureInfo.InvariantCulture));
                continue;
            }
            Check.True(IsAllowedPreGateStructuralOpcode(instruction.OpCode),
                "unexpected pre-Passive opcode in " + awakeMethod.Owner
                + "::" + awakeMethod.Name + ": " + instruction.OpCode.Name);
        }
    }

    private static bool IsAllowedPreGateCall(MethodCall call)
    {
        if (call.Owner.StartsWith(
                "SsrOracle.Plugin.<>c__DisplayClass", StringComparison.Ordinal)
            && call.Name == ".ctor") return true;
        return (call.Owner == "BepInEx.BaseUnityPlugin"
                && call.Name == "get_Logger")
            || (call.Owner == "SsrOracle.Plugin.BepInExLog"
                && call.Name == ".ctor")
            || (call.Owner == "PassiveLogReporter" && call.Name == ".ctor")
            || (call.Owner == "BepInEx.Paths"
                && call.Name == "get_ConfigPath")
            || (call.Owner == "System.IO.Path" && call.Name == "Combine")
            || (call.Owner == "OracleConfiguration" && call.Name == "Load")
            || (call.Owner == "OracleConfigurationException"
                && call.Name == "get_Code")
            || (call.Owner == "PassiveLogReporter" && call.Name == "Failed")
            || (call.Owner == "OracleConfiguration" && call.Name == "get_Mode")
            || (call.Owner == "System.Action" && call.Name == ".ctor")
            || (call.Owner == "PluginModePolicy" && call.Name == "StartOff");
    }

    private static bool IsReturnOffset(
        List<IlInstruction> instructions, int offset)
    {
        for (int index = 0; index < instructions.Count; index++)
            if (instructions[index].Offset == offset)
                return instructions[index].OpCode.Value == OpCodes.Ret.Value;
        return false;
    }

    private static bool IsAllowedPreGateStructuralOpcode(OpCode opcode)
    {
        string name = opcode.Name;
        return name == "nop" || name == "ldnull" || name == "dup"
            || name == "pop" || name == "ret" || name == "endfinally"
            || name.StartsWith("ldarg", StringComparison.Ordinal)
            || name.StartsWith("starg", StringComparison.Ordinal)
            || name.StartsWith("ldloc", StringComparison.Ordinal)
            || name.StartsWith("stloc", StringComparison.Ordinal)
            || name.StartsWith("ldc.i4", StringComparison.Ordinal);
    }

    private static string[] S(string name, string returnType, params string[] parameters)
    {
        string[] result = new string[parameters.Length + 2];
        result[0] = name; result[1] = returnType;
        Array.Copy(parameters, 0, result, 2, parameters.Length);
        return result;
    }

    private static void RequirePatch(
        MetadataImage image, string owner, string[][] expected)
    {
        MethodShape[] methods = image.AllMethods(owner);
        int callbacks = 0;
        for (int index = 0; index < methods.Length; index++)
            if (methods[index].Name != ".ctor" && methods[index].Name != "TargetMethod")
                callbacks++;
        Check.Equal(expected.Length, callbacks, owner + " callback count");
        for (int index = 0; index < expected.Length; index++)
        {
            string[] value = expected[index];
            ParameterShape[] parameters = new ParameterShape[value.Length - 2];
            for (int parameter = 0; parameter < parameters.Length; parameter++)
                parameters[parameter] = P(value[parameter + 2]);
            RequireMethod(image, owner, value[0], "private", true, value[1], parameters);
        }
    }

    private static void RequireTargetMethod(MetadataImage image,
        string patch, string targetOwner, string targetName, int flags,
        string returnType, params string[] parameterTypes)
    {
        MethodShape method = OnlyMethod(image, patch, "TargetMethod");
        List<IlInstruction> instructions = image.Instructions(method);
        List<string> typeTokens = new List<string>();
        List<string> strings = new List<string>();
        List<int> constants = new List<int>();
        int newArrays = 0;
        int stores = 0;
        for (int index = 0; index < instructions.Count; index++)
        {
            IlInstruction instruction = instructions[index];
            if (instruction.OpCode.Value == OpCodes.Ldtoken.Value)
                typeTokens.Add(image.TokenType(instruction));
            else if (instruction.OpCode.Value == OpCodes.Ldstr.Value)
                strings.Add(image.StringLiteral(instruction));
            else if (instruction.OpCode.Value == OpCodes.Newarr.Value)
            {
                Check.Equal("System.Type", image.TokenType(instruction),
                    patch + " parameter array element type");
                newArrays++;
            }
            else if (instruction.OpCode.Value == OpCodes.Stelem_Ref.Value)
                stores++;
            int constant;
            if (MetadataImage.TryConstant(instruction, out constant))
                constants.Add(constant);
        }
        string[] expectedTypes = new string[parameterTypes.Length + 2];
        expectedTypes[0] = targetOwner;
        expectedTypes[1] = returnType;
        Array.Copy(parameterTypes, 0, expectedTypes, 2, parameterTypes.Length);
        RequireSequence(expectedTypes, typeTokens.ToArray(),
            patch + " exact typeof vector");
        RequireSequence(new string[] { targetName }, strings.ToArray(),
            patch + " exact method name");
        int[] expectedConstants = new int[parameterTypes.Length + 2];
        expectedConstants[0] = flags;
        expectedConstants[1] = parameterTypes.Length;
        for (int index = 0; index < parameterTypes.Length; index++)
            expectedConstants[index + 2] = index;
        RequireIntSequence(expectedConstants, constants.ToArray(),
            patch + " exact BindingFlags and parameter indexes");
        Check.Equal(1, newArrays, patch + " exact parameter array");
        Check.Equal(parameterTypes.Length, stores,
            patch + " exact parameter array stores");
        RequireCallCount(image.Calls(method), "PatchTarget", "Require", 1,
            patch + " exact target helper");
        RequireLastCallThenReturn(image, method, "PatchTarget", "Require",
            patch + " returns exact target result");
    }

    private static void RequireObservedForwarding(MetadataImage image,
        string patch, string callback, string controllerMethod,
        string[] controllerParameters, string[] expectedFieldLoads)
    {
        MethodShape forwarding = ObservedDelegateTarget(
            image, patch, callback);
        List<MethodCall> calls = image.Calls(forwarding);
        MethodCall controllerCall = OnlyCall(calls, "OracleController",
            controllerMethod,
            patch + "::" + callback + " exact controller forwarding");
        RequireMethodCallSignature(controllerCall, controllerParameters,
            patch + "::" + callback + " forwarding signature");
        int controllerCalls = 0;
        for (int index = 0; index < calls.Count; index++)
            if (calls[index].Owner == "OracleController") controllerCalls++;
        Check.Equal(1, controllerCalls,
            patch + "::" + callback + " one controller call");
        List<string> fields = new List<string>();
        List<IlInstruction> instructions = image.Instructions(forwarding);
        for (int index = 0; index < instructions.Count; index++)
            if (instructions[index].OpCode.Value == OpCodes.Ldfld.Value)
                fields.Add(image.FieldName(instructions[index]));
        RequireSequence(expectedFieldLoads, fields.ToArray(),
            patch + "::" + callback + " runtime argument order");
    }

    private static MethodShape ObservedDelegateTarget(
        MetadataImage image, string patch, string callback)
    {
        MethodShape callbackMethod = OnlyMethod(image, patch, callback);
        List<MethodCall> calls = image.Calls(callbackMethod);
        MethodCall observe = OnlyCall(calls, "GameHooks", "Observe",
            patch + "::" + callback + " uses firewall");
        MethodCall action = null;
        for (int index = 0; index < calls.Count; index++)
            if (calls[index].Name == ".ctor"
                && calls[index].Owner == "System.Action<OracleController>")
            {
                Check.True(action == null,
                    patch + "::" + callback + " delegate construction duplicated");
                action = calls[index];
            }
        if (action == null) throw new InvalidOperationException(
            patch + "::" + callback + " delegate construction missing");
        List<IlInstruction> instructions = image.Instructions(callbackMethod);
        IlInstruction function = null;
        for (int index = 0; index < instructions.Count; index++)
            if (instructions[index].OpCode.Value == OpCodes.Ldftn.Value)
            {
                Check.True(function == null,
                    patch + "::" + callback + " delegate target duplicated");
                function = instructions[index];
            }
        if (function == null) throw new InvalidOperationException(
            patch + "::" + callback + " delegate target missing");
        int functionIndex = InstructionIndex(instructions, function.Offset);
        int actionIndex = InstructionIndex(instructions, action.Offset);
        int observeIndex = InstructionIndex(instructions, observe.Offset);
        bool direct = observeIndex == actionIndex + 1;
        bool exactCompilerCache = observeIndex == actionIndex + 3
            && instructions[actionIndex + 1].OpCode.Value == OpCodes.Dup.Value
            && instructions[actionIndex + 2].OpCode.Value == OpCodes.Stsfld.Value;
        Check.True(actionIndex == functionIndex + 1
            && (direct || exactCompilerCache),
            patch + "::" + callback
            + " contiguous delegate stack flow into Observe");
        MethodShape target = image.MethodFromToken(function);
        Check.True((target.Owner == patch
                || target.Owner.StartsWith(patch + ".", StringComparison.Ordinal))
            && target.Name.IndexOf(
                "<" + callback + ">", StringComparison.Ordinal) >= 0,
            patch + "::" + callback + " exact delegate target identity");
        return target;
    }

    private static void RequireTokenStateWriteBack(MetadataImage image,
        string patch, string enteredMethod, int outArgumentIndex)
    {
        MethodShape forwarding = ObservedDelegateTarget(image, patch, "Prefix");
        MethodCall entered = OnlyCall(image.Calls(forwarding),
            "OracleController", enteredMethod,
            patch + " entered forwarding result");
        List<IlInstruction> forwardingInstructions = image.Instructions(forwarding);
        int enteredIndex = InstructionIndex(forwardingInstructions, entered.Offset);
        Check.True(enteredIndex + 1 < forwardingInstructions.Count
            && forwardingInstructions[enteredIndex + 1].OpCode.Value
                == OpCodes.Stfld.Value
            && image.FieldName(forwardingInstructions[enteredIndex + 1]) == "token",
            patch + " entered result stored into captured token");
        int capturedToken = forwardingInstructions[enteredIndex + 1].Token;

        MethodShape prefix = OnlyMethod(image, patch, "Prefix");
        List<MethodCall> prefixCalls = image.Calls(prefix);
        MethodCall observe = OnlyCall(prefixCalls, "GameHooks", "Observe",
            patch + " observe call");
        MethodCall inert = OnlyCallBefore(prefixCalls, "HookToken", "Inert",
            observe.Offset, patch + " pre-Observe inert call");
        List<IlInstruction> instructions = image.Instructions(prefix);
        int inertIndex = InstructionIndex(instructions, inert.Offset);
        Check.True(inertIndex + 1 < instructions.Count
            && instructions[inertIndex + 1].OpCode.Value == OpCodes.Stfld.Value
            && image.FieldName(instructions[inertIndex + 1]) == "token"
            && instructions[inertIndex + 1].Token == capturedToken,
            patch + " inert token stored into captured token");
        int observeIndex = InstructionIndex(instructions, observe.Offset);
        Check.True(observeIndex + 6 == instructions.Count,
            patch + " exact post-Observe out-state sequence length");
        int stateArgument = -1;
        Check.True(MetadataImage.TryArgumentIndex(
            instructions[observeIndex + 1], out stateArgument),
            patch + " immediate out __state argument load");
        Check.Equal(outArgumentIndex, stateArgument,
            patch + " exact Harmony out __state argument");
        Check.True(IsLocalLoad(instructions[observeIndex + 2].OpCode)
            && instructions[observeIndex + 3].OpCode.Value == OpCodes.Ldfld.Value
            && image.FieldName(instructions[observeIndex + 3]) == "token"
            && instructions[observeIndex + 3].Token == capturedToken
            && instructions[observeIndex + 4].OpCode.Value == OpCodes.Stind_Ref.Value
            && instructions[observeIndex + 5].OpCode.Value == OpCodes.Ret.Value,
            patch + " contiguous captured token store through out __state");
    }

    private static bool IsLocalLoad(OpCode opcode)
    {
        return opcode.Name == "ldloc" || opcode.Name == "ldloc.s"
            || opcode.Name == "ldloc.0" || opcode.Name == "ldloc.1"
            || opcode.Name == "ldloc.2" || opcode.Name == "ldloc.3";
    }

    private static bool TryLocalAddressIndex(
        IlInstruction instruction, out int value)
    {
        value = 0;
        short opcode = instruction.OpCode.Value;
        if ((opcode == OpCodes.Ldloca.Value
                || opcode == OpCodes.Ldloca_S.Value)
            && instruction.HasVariable)
        {
            value = instruction.VariableIndex;
            return true;
        }
        return false;
    }

    private static bool TryLocalLoadIndex(
        IlInstruction instruction, out int value)
    {
        value = 0;
        short opcode = instruction.OpCode.Value;
        if (opcode == OpCodes.Ldloc_0.Value) return true;
        if (opcode == OpCodes.Ldloc_1.Value) { value = 1; return true; }
        if (opcode == OpCodes.Ldloc_2.Value) { value = 2; return true; }
        if (opcode == OpCodes.Ldloc_3.Value) { value = 3; return true; }
        if ((opcode == OpCodes.Ldloc.Value || opcode == OpCodes.Ldloc_S.Value)
            && instruction.HasVariable)
        {
            value = instruction.VariableIndex;
            return true;
        }
        return false;
    }

    private static bool TryLocalStoreIndex(
        IlInstruction instruction, out int value)
    {
        value = 0;
        short opcode = instruction.OpCode.Value;
        if (opcode == OpCodes.Stloc_0.Value) return true;
        if (opcode == OpCodes.Stloc_1.Value) { value = 1; return true; }
        if (opcode == OpCodes.Stloc_2.Value) { value = 2; return true; }
        if (opcode == OpCodes.Stloc_3.Value) { value = 3; return true; }
        if ((opcode == OpCodes.Stloc.Value || opcode == OpCodes.Stloc_S.Value)
            && instruction.HasVariable)
        {
            value = instruction.VariableIndex;
            return true;
        }
        return false;
    }

    private static void RequirePlayerInputPrefixControlFlow(
        MetadataImage image, MethodShape prefix)
    {
        List<MethodCall> calls = image.Calls(prefix);
        MethodCall gate = OnlyCall(calls, "GameHooks",
            "TryOverridePlayerInput", "Playerinputstring replay gate");
        List<IlInstruction> instructions = image.Instructions(prefix);
        int gateIndex = InstructionIndex(instructions, gate.Offset);
        int rawLocal = -1;
        Check.True(gateIndex > 0
            && TryLocalAddressIndex(instructions[gateIndex - 1], out rawLocal),
            "Playerinputstring gate receives one raw-direction local by address");
        Check.True(gateIndex + 1 < instructions.Count,
            "Playerinputstring gate result has a consumer");

        IlInstruction branch = instructions[gateIndex + 1];
        bool branchesOnTrue = branch.OpCode.Value == OpCodes.Brtrue.Value
            || branch.OpCode.Value == OpCodes.Brtrue_S.Value;
        bool branchesOnFalse = branch.OpCode.Value == OpCodes.Brfalse.Value
            || branch.OpCode.Value == OpCodes.Brfalse_S.Value;
        Check.True(branch.HasBranchTarget
            && (branchesOnTrue || branchesOnFalse),
            "Playerinputstring gate result immediately controls two paths");

        int fallthrough = gateIndex + 2;
        int target = InstructionIndex(instructions, branch.BranchTarget);
        int falseGate = branchesOnFalse ? target : fallthrough;
        int trueGate = branchesOnTrue ? target : fallthrough;
        RequireLiteralReturnPath(instructions, falseGate, 1,
            "false Playerinputstring gate preserves native execution");
        RequireRawDirectionStorePath(image, instructions, trueGate, rawLocal);
    }

    private static void RequireLiteralReturnPath(
        List<IlInstruction> instructions, int start, int value, string message)
    {
        int actual = 0;
        Check.True(start >= 0 && start + 1 < instructions.Count
            && MetadataImage.TryConstant(instructions[start], out actual)
            && actual == value
            && instructions[start + 1].OpCode.Value == OpCodes.Ret.Value,
            message);
    }

    private static void RequireRawDirectionStorePath(MetadataImage image,
        List<IlInstruction> instructions, int start, int rawLocal)
    {
        int resultArgument = -1;
        int storedLocal = -1;
        int returnValue = -1;
        Check.True(start >= 0 && start + 4 < instructions.Count
            && MetadataImage.TryArgumentIndex(
                instructions[start], out resultArgument)
            && resultArgument == 0
            && TryLocalLoadIndex(instructions[start + 1], out storedLocal)
            && storedLocal == rawLocal,
            "true Playerinputstring gate loads __result and exact raw local");
        bool exactStore = instructions[start + 2].OpCode.Value
                == OpCodes.Stind_I4.Value
            || (instructions[start + 2].OpCode.Value == OpCodes.Stobj.Value
                && image.TokenType(instructions[start + 2]) == "Direction");
        Check.True(exactStore
            && MetadataImage.TryConstant(
                instructions[start + 3], out returnValue)
            && returnValue == 0
            && instructions[start + 4].OpCode.Value == OpCodes.Ret.Value,
            "true Playerinputstring gate stores raw result and skips native execution");
    }

    private static void RequireReplayControllerRouting(MetadataImage image)
    {
        RequireSoleCallOrder(image, "PhysicalPollReturned", new string[]
        {
            "ReplayCoordinator", "PhysicalPollReturned",
            "PassiveDriver", "PhysicalPollReturned"
        });
        RequireSoleCallOrder(image, "ProcessInputEntered", new string[]
        {
            "ReplayCoordinator", "ProcessInputEntered",
            "IOracleRuntimeHost", "NowSeconds",
            "PassiveDriver", "ProcessInputEntered"
        });
        RequireSoleCallOrder(image, "UndoEntered", new string[]
        {
            "ReplayCoordinator", "UndoEntered",
            "IOracleGameAdapter", "TryGetState",
            "IOracleRuntimeHost", "NowSeconds",
            "PassiveDriver", "UndoEntered"
        });
        RequireSoleCallOrder(image, "RestoreObserved", new string[]
        {
            "ReplayCoordinator", "RestoreObserved",
            "PassiveDriver", "RestoreObserved"
        });
        RequireSoleCallOrder(image, "UndoReturned", new string[]
        {
            "ReplayCoordinator", "UndoReturned",
            "IOracleGameAdapter", "CurrentMovementScheduled",
            "PassiveDriver", "UndoReturned"
        });
    }

    private static void RequireSoleCallOrder(MetadataImage image,
        string methodName, string[] ownerAndName)
    {
        Check.True(ownerAndName.Length > 0
            && ownerAndName.Length % 2 == 0,
            methodName + " route expectation is paired");
        List<MethodCall> calls = image.Calls(OnlyMethod(
            image, "OracleController", methodName));
        int priorOffset = -1;
        for (int index = 0; index < ownerAndName.Length; index += 2)
        {
            string owner = ownerAndName[index];
            string name = ownerAndName[index + 1];
            MethodCall call = OnlyCall(calls, owner, name,
                "OracleController::" + methodName + " sole "
                + owner + "::" + name + " route");
            Check.True(call.Offset > priorOffset,
                "OracleController::" + methodName
                + " exact coordinator-first route order");
            priorOffset = call.Offset;
        }
    }

    private static void RequireInertBeforeObserve(
        MetadataImage image, string patch, int expectedKind)
    {
        MethodShape prefix = OnlyMethod(image, patch, "Prefix");
        List<MethodCall> calls = image.Calls(prefix);
        MethodCall inert = OnlyCall(calls, "HookToken", "Inert",
            patch + " inert initialization");
        MethodCall observe = OnlyCall(calls, "GameHooks", "Observe",
            patch + " firewall");
        Check.True(inert.Offset < observe.Offset,
            patch + " inert token precedes observation");
        List<IlInstruction> instructions = image.Instructions(prefix);
        int inertIndex = InstructionIndex(instructions, inert.Offset);
        int actual = 0;
        Check.True(inertIndex > 0
            && MetadataImage.TryConstant(instructions[inertIndex - 1], out actual),
            patch + " inert kind is a literal");
        Check.Equal(expectedKind, actual, patch + " exact inert HookKind");
    }

    private static void RequireDirectReturnCall(MetadataImage image,
        string owner, string methodName, string callOwner, string callName,
        int[] argumentIndexes)
    {
        MethodShape method = OnlyMethod(image, owner, methodName);
        List<MethodCall> calls = image.Calls(method);
        MethodCall call = OnlyCall(calls, callOwner, callName,
            owner + "::" + methodName + " exact return call");
        List<IlInstruction> instructions = image.Instructions(method);
        int callIndex = InstructionIndex(instructions, call.Offset);
        Check.True(callIndex >= argumentIndexes.Length,
            owner + "::" + methodName + " argument count");
        for (int index = 0; index < argumentIndexes.Length; index++)
        {
            int actual;
            Check.True(MetadataImage.TryArgumentIndex(
                instructions[callIndex - argumentIndexes.Length + index],
                out actual), owner + "::" + methodName + " argument load");
            Check.Equal(argumentIndexes[index], actual,
                owner + "::" + methodName + " argument order");
        }
        Check.True(callIndex + 1 < instructions.Count
            && instructions[callIndex + 1].OpCode.Value == OpCodes.Ret.Value
            && callIndex + 2 == instructions.Count,
            owner + "::" + methodName + " returns call result unchanged");
    }

    private static void RequireTrueReturn(
        MetadataImage image, string owner, string methodName)
    {
        List<IlInstruction> instructions = image.Instructions(
            OnlyMethod(image, owner, methodName));
        int value = 0;
        Check.True(instructions.Count == 2
            && MetadataImage.TryConstant(instructions[0], out value)
            && value == 1
            && instructions[1].OpCode.Value == OpCodes.Ret.Value,
            owner + "::" + methodName + " returns literal true");
    }

    private static void RequireNoOp(MetadataImage image,
        string owner, string methodName, string message)
    {
        List<IlInstruction> instructions = image.Instructions(
            OnlyMethod(image, owner, methodName));
        Check.True(instructions.Count == 1
            && instructions[0].OpCode.Value == OpCodes.Ret.Value, message);
    }

    private static MethodCall OnlyCall(List<MethodCall> calls,
        string owner, string name, string message)
    {
        MethodCall found = null;
        for (int index = 0; index < calls.Count; index++)
        {
            if (calls[index].Owner != owner || calls[index].Name != name) continue;
            Check.True(found == null, message + " is duplicated");
            found = calls[index];
        }
        if (found == null) throw new InvalidOperationException(message + " is missing");
        return found;
    }

    private static MethodCall OnlyCallBefore(List<MethodCall> calls,
        string owner, string name, int beforeOffset, string message)
    {
        MethodCall found = null;
        for (int index = 0; index < calls.Count; index++)
        {
            if (calls[index].Offset >= beforeOffset
                || calls[index].Owner != owner || calls[index].Name != name)
                continue;
            Check.True(found == null, message + " is duplicated");
            found = calls[index];
        }
        if (found == null) throw new InvalidOperationException(message + " is missing");
        return found;
    }

    private static List<MethodCall> CallsNamed(
        List<MethodCall> calls, string owner, string name)
    {
        List<MethodCall> result = new List<MethodCall>();
        for (int index = 0; index < calls.Count; index++)
            if (calls[index].Owner == owner && calls[index].Name == name)
                result.Add(calls[index]);
        return result;
    }

    private static int FindConditionalBranch(List<IlInstruction> instructions,
        int afterOffset, int beforeOffset, string message)
    {
        int found = -1;
        for (int index = 0; index < instructions.Count; index++)
        {
            IlInstruction instruction = instructions[index];
            if (instruction.Offset <= afterOffset
                || instruction.Offset >= beforeOffset
                || instruction.OpCode.FlowControl != FlowControl.Cond_Branch)
                continue;
            Check.True(instruction.HasBranchTarget,
                message + " has a decoded target");
            Check.Equal(-1, found, message + " is unique");
            found = index;
        }
        if (found < 0) throw new InvalidOperationException(message + " is missing");
        return found;
    }

    private static int FirstConditionalBranchAfter(
        List<IlInstruction> instructions, int afterOffset, string message)
    {
        for (int index = 0; index < instructions.Count; index++)
            if (instructions[index].Offset > afterOffset
                && instructions[index].OpCode.FlowControl
                    == FlowControl.Cond_Branch)
            {
                Check.True(instructions[index].HasBranchTarget,
                    message + " has a decoded target");
                return index;
            }
        throw new InvalidOperationException(message + " is missing");
    }

    private static bool HasReturnBetween(List<IlInstruction> instructions,
        int afterOffset, int beforeOffset)
    {
        for (int index = 0; index < instructions.Count; index++)
            if (instructions[index].Offset > afterOffset
                && instructions[index].Offset < beforeOffset
                && instructions[index].OpCode.Value == OpCodes.Ret.Value)
                return true;
        return false;
    }

    private static void RequireMethodCallSignature(
        MethodCall call, string[] parameters, string message)
    {
        Check.Equal(parameters.Length, call.Parameters.Length, message + " count");
        for (int index = 0; index < parameters.Length; index++)
            Check.Equal(parameters[index], call.Parameters[index],
                message + "[" + index.ToString(CultureInfo.InvariantCulture) + "]");
    }

    private static int InstructionIndex(
        List<IlInstruction> instructions, int offset)
    {
        for (int index = 0; index < instructions.Count; index++)
            if (instructions[index].Offset == offset) return index;
        throw new InvalidOperationException("missing IL instruction offset");
    }

    private static void RequireLastCallThenReturn(MetadataImage image,
        MethodShape method, string owner, string name, string message)
    {
        MethodCall call = OnlyCall(image.Calls(method), owner, name, message);
        List<IlInstruction> instructions = image.Instructions(method);
        int index = InstructionIndex(instructions, call.Offset);
        Check.True(index + 1 < instructions.Count
            && instructions[index + 1].OpCode.Value == OpCodes.Ret.Value
            && index + 2 == instructions.Count, message);
    }

    private static void RequireIntSequence(
        int[] expected, int[] actual, string message)
    {
        Check.Equal(expected.Length, actual.Length, message + " length");
        for (int index = 0; index < expected.Length; index++)
            Check.Equal(expected[index], actual[index],
                message + "[" + index.ToString(CultureInfo.InvariantCulture) + "]");
    }

    private static MethodShape OnlyMethod(
        MetadataImage image, string owner, string name)
    {
        MethodShape[] methods = image.Methods(owner, name);
        Check.Equal(1, methods.Length, owner + "::" + name + " count");
        return methods[0];
    }

    private static void RequireOrderedCalls(
        List<MethodCall> actual, string[] expected, string message)
    {
        int next = 0;
        for (int index = 0; index < actual.Count && next < expected.Length; index++)
            if (actual[index].Owner + "::" + actual[index].Name == expected[next]) next++;
        Check.Equal(expected.Length, next, message);
    }

    private static void RequireCallCount(List<MethodCall> calls,
        string owner, string name, int expected, string message)
    {
        int count = 0;
        for (int index = 0; index < calls.Count; index++)
            if (calls[index].Owner == owner && calls[index].Name == name) count++;
        Check.Equal(expected, count, message);
    }

    private static void RequireSequence(
        string[] expected, string[] actual, string message)
    {
        Check.Equal(expected.Length, actual.Length, message + " length");
        for (int index = 0; index < expected.Length; index++)
            Check.Equal(expected[index], actual[index],
                message + "[" + index.ToString(CultureInfo.InvariantCulture) + "]");
    }

    private static void RequireFalseFalseBeforeSave(MetadataImage image, MethodShape method)
    {
        List<IlInstruction> values = image.Instructions(method);
        for (int index = 0; index < values.Count; index++)
        {
            IlInstruction instruction = values[index];
            if (instruction.OpCode.Value != OpCodes.Callvirt.Value && instruction.OpCode.Value != OpCodes.Call.Value) continue;
            MethodCall call = image.Calls(method).Find(delegate(MethodCall value) { return value.Offset == instruction.Offset; });
            if (call == null || call.Owner != "GameState" || call.Name != "Save") continue;
            int first; int second;
            if (index < 2 || !MetadataImage.TryConstant(values[index - 2], out first)
                || !MetadataImage.TryConstant(values[index - 1], out second)
                || first != 0 || second != 0)
                throw new InvalidOperationException("Save arguments are not false,false");
            return;
        }
        throw new InvalidOperationException("Save call is missing");
    }

    private static void RequireGameCall(List<MethodCall> calls, string owner,
        string name, string returnType, string[] parameters)
    {
        int matches = 0;
        for (int index = 0; index < calls.Count; index++)
        {
            MethodCall call = calls[index];
            if (call.Owner != owner || call.Name != name || call.ReturnType != returnType
                || call.Parameters.Length != parameters.Length) continue;
            bool same = true;
            for (int parameter = 0; parameter < parameters.Length; parameter++)
                same &= call.Parameters[parameter] == parameters[parameter];
            if (same) matches++;
        }
        Check.Equal(1, matches, owner + "::" + name);
    }

    private static void RequireMethod(MetadataImage image, string owner,
        string name, string visibility, bool isStatic, string returnType,
        params ParameterShape[] parameters)
    { RequireMethodShape(image.Methods(owner, name), new MethodShape(default(MethodDefinitionHandle), owner, name, visibility, isStatic, returnType, parameters)); }
    private static MethodShape RequireSoleMethod(MetadataImage image,
        string owner, string name, string visibility, bool isStatic,
        string returnType, params ParameterShape[] parameters)
    {
        MethodShape[] methods = image.Methods(owner, name);
        Check.Equal(1, methods.Length, owner + "::" + name + " exact overload count");
        return RequireMethodShape(methods, new MethodShape(
            default(MethodDefinitionHandle), owner, name, visibility, isStatic,
            returnType, parameters));
    }
    private static void RequireField(MetadataImage image, string owner,
        string name, string visibility, bool isStatic, string fieldType)
    { RequireFieldShape(image.Fields(owner, name), new FieldShape(owner, name, visibility, isStatic, fieldType)); }
    private static void RequireEnumShape(EnumShape[] actual, EnumShape expected)
    { for (int i = 0; i < actual.Length; i++) if (actual[i].Name == expected.Name && actual[i].Value == expected.Value) return; throw new InvalidOperationException("missing enum shape"); }
    internal static MethodShape RequireMethodShape(MethodShape[] actual, MethodShape expected)
    { MethodShape found = null; for (int i = 0; i < actual.Length; i++) { MethodShape value = actual[i]; if (!MethodMatches(value, expected)) continue; if (found != null) throw new InvalidOperationException("duplicate method shape"); found = value; } if (found == null) throw new InvalidOperationException("missing method shape"); return found; }
    internal static FieldShape RequireFieldShape(FieldShape[] actual, FieldShape expected)
    { FieldShape found = null; for (int i = 0; i < actual.Length; i++) { FieldShape value = actual[i]; if (value.Owner != expected.Owner || value.Name != expected.Name || value.Visibility != expected.Visibility || value.IsStatic != expected.IsStatic || value.FieldType != expected.FieldType) continue; if (found != null) throw new InvalidOperationException("duplicate field shape"); found = value; } if (found == null) throw new InvalidOperationException("missing field shape"); return found; }
    private static bool MethodMatches(MethodShape actual, MethodShape expected)
    { if (actual.Owner != expected.Owner || actual.Name != expected.Name || actual.Visibility != expected.Visibility || actual.IsStatic != expected.IsStatic || actual.ReturnType != expected.ReturnType || actual.Parameters.Length != expected.Parameters.Length) return false; for (int i = 0; i < actual.Parameters.Length; i++) if (actual.Parameters[i].Type != expected.Parameters[i].Type) return false; return true; }
}
