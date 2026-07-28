using System.Reflection;
using System.Reflection.Emit;
using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;
using System.Text.Json;

internal static class Program
{
    private const string TargetFrameworkAttributeName = "TargetFrameworkAttribute";
    private const string TargetFrameworkAttributeNamespace = "System.Runtime.Versioning";
    private static readonly IReadOnlyDictionary<string, string> LegacyReferences =
        new SortedDictionary<string, string>(StringComparer.Ordinal)
        {
            ["0Harmony"] = "2.9.0.0",
            ["BepInEx"] = "5.4.23.5",
            ["HarmonyXInterop"] = "1.0.0.0",
            ["Mono.Cecil"] = "0.10.4.0",
            ["MonoMod.RuntimeDetour"] = "22.1.29.1",
            ["MonoMod.Utils"] = "22.1.29.1",
            ["System"] = "2.0.0.0",
            ["System.Core"] = "3.5.0.0",
            ["mscorlib"] = "2.0.0.0",
        };

    public static int Main(string[] args)
    {
        bool requirePlatformPatch = args.Length == 2
            && args[0] == "--require-platform-patch";
        if (args.Length != 1 && !requirePlatformPatch)
        {
            Console.Error.WriteLine(
                "usage: SsrOracle.CompatInspector [--require-platform-patch] <assembly.dll>");
            return 2;
        }

        try
        {
            Inspect(args[^1], Console.OpenStandardOutput(), requirePlatformPatch);
            return 0;
        }
        catch (Exception error) when (
            error is IOException
            or UnauthorizedAccessException
            or BadImageFormatException
            or InvalidOperationException
            or ArgumentException)
        {
            Console.Error.WriteLine($"invalid managed assembly: {error.Message}");
            return 2;
        }
    }

    private static void Inspect(
        string path,
        Stream output,
        bool requirePlatformPatch)
    {
        using FileStream stream = File.OpenRead(path);
        using PEReader pe = new(stream, PEStreamOptions.LeaveOpen);
        if (!pe.HasMetadata || pe.PEHeaders.CorHeader is null)
        {
            throw new BadImageFormatException("CLI metadata is missing");
        }

        CorFlags flags = pe.PEHeaders.CorHeader.Flags;
        if (!flags.HasFlag(CorFlags.ILOnly) || flags.HasFlag(CorFlags.NativeEntryPoint))
        {
            throw new BadImageFormatException("native or mixed-mode image");
        }
        DirectoryEntry managedNative =
            pe.PEHeaders.CorHeader.ManagedNativeHeaderDirectory;
        if (managedNative.RelativeVirtualAddress != 0 || managedNative.Size != 0)
        {
            throw new BadImageFormatException("managed-native header is present");
        }

        MetadataReader metadata = pe.GetMetadataReader();
        if (!metadata.IsAssembly)
        {
            throw new BadImageFormatException("metadata is not an assembly");
        }

        AssemblyDefinition definition = metadata.GetAssemblyDefinition();
        string assemblyName = RequiredString(metadata, definition.Name, "assembly name");
        SortedDictionary<string, string> references = ReadReferences(metadata);
        string targetFramework = ReadTargetFramework(
            metadata,
            definition,
            references);
        if (requirePlatformPatch)
        {
            RequirePlatformPatch(pe, metadata);
        }

        using Utf8JsonWriter writer = new(
            output,
            new JsonWriterOptions { Indented = true });
        writer.WriteStartObject();
        writer.WriteString("assembly_name", assemblyName);
        writer.WriteString("assembly_version", definition.Version.ToString());
        writer.WriteString("metadata_version", metadata.MetadataVersion);
        writer.WritePropertyName("references");
        writer.WriteStartObject();
        foreach ((string name, string version) in references)
        {
            writer.WriteString(name, version);
        }
        writer.WriteEndObject();
        writer.WriteString("target_framework", targetFramework);
        writer.WriteEndObject();
        writer.Flush();
        output.WriteByte((byte)'\n');
    }

    private static void RequirePlatformPatch(
        PEReader pe,
        MetadataReader metadata)
    {
        List<MethodDefinitionHandle> matches = [];
        foreach (TypeDefinitionHandle typeHandle in metadata.TypeDefinitions)
        {
            TypeDefinition type = metadata.GetTypeDefinition(typeHandle);
            if (metadata.GetString(type.Name) != "PlatformUtils"
                || metadata.GetString(type.Namespace) != "BepInEx.Preloader")
            {
                continue;
            }
            foreach (MethodDefinitionHandle methodHandle in type.GetMethods())
            {
                MethodDefinition method = metadata.GetMethodDefinition(methodHandle);
                if (metadata.GetString(method.Name) == "SetPlatform")
                {
                    matches.Add(methodHandle);
                }
            }
        }
        if (matches.Count != 1)
        {
            throw new BadImageFormatException(
                "expected exactly one PlatformUtils.SetPlatform method");
        }

        MethodDefinition target = metadata.GetMethodDefinition(matches[0]);
        if (target.RelativeVirtualAddress == 0)
        {
            throw new BadImageFormatException("platform method has no IL body");
        }
        BlobReader il = pe.GetMethodBody(target.RelativeVirtualAddress).GetILReader();
        int coreServices = 0;
        int accessibilityBundles = 0;
        while (il.RemainingBytes > 0)
        {
            ushort code = il.ReadByte();
            if (code == 0xfe)
            {
                code = (ushort)(0xfe00 | il.ReadByte());
            }
            if (!OperandTypes.TryGetValue(code, out OperandType operandType))
            {
                throw new BadImageFormatException($"unknown IL opcode: 0x{code:x4}");
            }
            if (code == 0x72)
            {
                int token = il.ReadInt32();
                if ((token & unchecked((int)0xff000000)) != 0x70000000)
                {
                    throw new BadImageFormatException("invalid IL string token");
                }
                string value = metadata.GetUserString(
                    MetadataTokens.UserStringHandle(token & 0x00ffffff));
                if (value == "/System/Library/CoreServices")
                {
                    coreServices++;
                }
                else if (value == "/System/Library/AccessibilityBundles")
                {
                    accessibilityBundles++;
                }
                continue;
            }
            SkipOperand(ref il, operandType);
        }
        if (coreServices != 1 || accessibilityBundles != 0)
        {
            throw new BadImageFormatException(
                "platform method does not contain the exact macOS patch marker");
        }
    }

    private static Dictionary<ushort, OperandType> CreateOperandTypes()
    {
        Dictionary<ushort, OperandType> result = [];
        foreach (FieldInfo field in typeof(OpCodes).GetFields(
            BindingFlags.Public | BindingFlags.Static))
        {
            if (field.GetValue(null) is OpCode opcode)
            {
                result[unchecked((ushort)opcode.Value)] = opcode.OperandType;
            }
        }
        return result;
    }

    private static readonly Dictionary<ushort, OperandType> OperandTypes =
        CreateOperandTypes();

    private static void SkipOperand(ref BlobReader reader, OperandType operandType)
    {
        int bytes = operandType switch
        {
            OperandType.InlineNone => 0,
            OperandType.ShortInlineBrTarget
                or OperandType.ShortInlineI
                or OperandType.ShortInlineVar => 1,
            OperandType.InlineVar => 2,
            OperandType.InlineBrTarget
                or OperandType.InlineField
                or OperandType.InlineI
                or OperandType.InlineMethod
                or OperandType.InlineSig
                or OperandType.InlineString
                or OperandType.InlineTok
                or OperandType.InlineType
                or OperandType.ShortInlineR => 4,
            OperandType.InlineI8 or OperandType.InlineR => 8,
            OperandType.InlineSwitch => checked(4 + 4 * reader.ReadInt32()),
            _ => throw new BadImageFormatException("unsupported IL operand"),
        };
        if (operandType == OperandType.InlineSwitch)
        {
            bytes -= 4;
        }
        if (bytes < 0 || reader.RemainingBytes < bytes)
        {
            throw new BadImageFormatException("truncated IL operand");
        }
        reader.ReadBytes(bytes);
    }

    private static SortedDictionary<string, string> ReadReferences(
        MetadataReader metadata)
    {
        SortedDictionary<string, string> result = new(StringComparer.Ordinal);
        foreach (AssemblyReferenceHandle handle in metadata.AssemblyReferences)
        {
            AssemblyReference reference = metadata.GetAssemblyReference(handle);
            string name = RequiredString(metadata, reference.Name, "reference name");
            if (!result.TryAdd(name, reference.Version.ToString()))
            {
                throw new BadImageFormatException($"duplicate assembly reference: {name}");
            }
        }
        return result;
    }

    private static string ReadTargetFramework(
        MetadataReader metadata,
        AssemblyDefinition definition,
        IReadOnlyDictionary<string, string> references)
    {
        string? result = null;
        foreach (CustomAttributeHandle handle in definition.GetCustomAttributes())
        {
            CustomAttribute attribute = metadata.GetCustomAttribute(handle);
            if (!IsTargetFrameworkAttribute(metadata, attribute.Constructor))
            {
                continue;
            }
            if (result is not null)
            {
                throw new BadImageFormatException("duplicate target framework metadata");
            }

            BlobReader reader = metadata.GetBlobReader(attribute.Value);
            if (reader.ReadUInt16() != 1)
            {
                throw new BadImageFormatException("malformed target framework metadata");
            }
            result = reader.ReadSerializedString();
            if (string.IsNullOrEmpty(result)
                || reader.ReadUInt16() != 0
                || reader.RemainingBytes != 0)
            {
                throw new BadImageFormatException("malformed target framework metadata");
            }
        }
        if (result is not null)
        {
            return result;
        }
        if (metadata.MetadataVersion == "v2.0.50727"
            && metadata.GetString(definition.Name) == "BepInEx.Preloader"
            && definition.Version == new Version(5, 4, 23, 5)
            && references.Count == LegacyReferences.Count
            && LegacyReferences.All(
                expected => references.TryGetValue(
                    expected.Key,
                    out string? version)
                    && version == expected.Value))
        {
            return ".NETFramework,Version=v3.5";
        }
        throw new BadImageFormatException("target framework metadata is missing");
    }

    private static bool IsTargetFrameworkAttribute(
        MetadataReader metadata,
        EntityHandle constructor)
    {
        EntityHandle type;
        if (constructor.Kind == HandleKind.MemberReference)
        {
            type = metadata.GetMemberReference(
                (MemberReferenceHandle)constructor).Parent;
        }
        else if (constructor.Kind == HandleKind.MethodDefinition)
        {
            type = metadata.GetMethodDefinition(
                (MethodDefinitionHandle)constructor).GetDeclaringType();
        }
        else
        {
            return false;
        }

        return type.Kind switch
        {
            HandleKind.TypeReference => Matches(
                metadata,
                metadata.GetTypeReference((TypeReferenceHandle)type).Name,
                metadata.GetTypeReference((TypeReferenceHandle)type).Namespace),
            HandleKind.TypeDefinition => Matches(
                metadata,
                metadata.GetTypeDefinition((TypeDefinitionHandle)type).Name,
                metadata.GetTypeDefinition((TypeDefinitionHandle)type).Namespace),
            _ => false,
        };
    }

    private static bool Matches(
        MetadataReader metadata,
        StringHandle name,
        StringHandle @namespace)
    {
        return metadata.GetString(name) == TargetFrameworkAttributeName
            && metadata.GetString(@namespace) == TargetFrameworkAttributeNamespace;
    }

    private static string RequiredString(
        MetadataReader metadata,
        StringHandle handle,
        string label)
    {
        string value = metadata.GetString(handle);
        return string.IsNullOrEmpty(value)
            ? throw new BadImageFormatException($"{label} is missing")
            : value;
    }
}
