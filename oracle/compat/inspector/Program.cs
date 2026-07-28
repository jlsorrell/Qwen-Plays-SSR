using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Text.Json;

internal static class Program
{
    private const string TargetFrameworkAttributeName = "TargetFrameworkAttribute";
    private const string TargetFrameworkAttributeNamespace = "System.Runtime.Versioning";

    public static int Main(string[] args)
    {
        if (args.Length != 1)
        {
            Console.Error.WriteLine("usage: SsrOracle.CompatInspector <assembly.dll>");
            return 2;
        }

        try
        {
            Inspect(args[0], Console.OpenStandardOutput());
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

    private static void Inspect(string path, Stream output)
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
            && references.TryGetValue("mscorlib", out string? mscorlib)
            && mscorlib == "2.0.0.0"
            && references.TryGetValue("System.Core", out string? systemCore)
            && systemCore == "3.5.0.0")
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
