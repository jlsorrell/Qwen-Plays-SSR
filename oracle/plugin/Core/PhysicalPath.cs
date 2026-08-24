using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

internal enum PhysicalPathKind { Missing, Directory, File, Symlink, Other }
internal sealed class PhysicalPathIdentity
{
    internal PhysicalPathIdentity(string canonicalPath, bool exists, string existingAncestor, string[] missingComponents)
    { CanonicalPath = canonicalPath; Exists = exists; ExistingAncestor = existingAncestor; MissingComponents = missingComponents; }
    internal string CanonicalPath { get; private set; }
    internal bool Exists { get; private set; }
    internal string ExistingAncestor { get; private set; }
    internal string[] MissingComponents { get; private set; }
}
internal interface IPhysicalPathOperations { PhysicalPathKind Classify(string absolutePath); string RealPath(string existingPath); }
internal static class PhysicalPath
{
    private sealed class ScanResult
    {
        internal PhysicalPathIdentity Identity;
        internal PhysicalPathKind FinalKind;
    }
    internal static string ResolveExistingDirectory(string requested) { return ResolveExistingDirectory(requested, MacPhysicalPathOperations.Instance, null); }
    internal static string ResolveExistingFile(string requested) { return ResolveExistingFile(requested, MacPhysicalPathOperations.Instance, null); }
    internal static PhysicalPathIdentity ResolvePossiblyAbsent(string requested) { return ResolvePossiblyAbsent(requested, MacPhysicalPathOperations.Instance, null); }
    internal static bool Contains(string parent, string candidate) { if (parent == "/") return candidate.StartsWith("/", StringComparison.Ordinal); return candidate == parent || candidate.StartsWith(parent + "/", StringComparison.Ordinal); }
    internal static string ResolveExistingDirectory(string requested, IPhysicalPathOperations operations, Action betweenScans)
    { ScanResult result = Resolve(requested, operations, betweenScans); if (!result.Identity.Exists || result.FinalKind != PhysicalPathKind.Directory) throw Failure(new IOException("directory does not exist")); return result.Identity.CanonicalPath; }
    internal static string ResolveExistingFile(string requested, IPhysicalPathOperations operations, Action betweenScans)
    { ScanResult result = Resolve(requested, operations, betweenScans); if (!result.Identity.Exists || result.FinalKind != PhysicalPathKind.File) throw Failure(new IOException("file does not exist")); return result.Identity.CanonicalPath; }
    internal static PhysicalPathIdentity ResolvePossiblyAbsent(string requested, IPhysicalPathOperations operations, Action betweenScans)
    { return Resolve(requested, operations, betweenScans).Identity; }
    private static ScanResult Resolve(string requested, IPhysicalPathOperations operations, Action betweenScans)
    { try { ValidateLexical(requested); if (operations == null) throw new ArgumentNullException("operations"); ScanResult first = Scan(requested, operations); if (betweenScans != null) betweenScans(); ScanResult second = Scan(requested, operations); if (!Same(first, second)) throw new IOException("path changed during authentication"); return second; } catch (OracleConfigurationException) { throw; } catch (Exception error) { throw Failure(error); } }
    private static ScanResult Scan(string requested, IPhysicalPathOperations operations)
    {
        string[] pieces = requested == "/" ? new string[0] : requested.Substring(1).Split('/');
        string current = "/"; PhysicalPathKind root = operations.Classify(current);
        if (root != PhysicalPathKind.Directory) throw new IOException("root is not a directory");
        int missingStart = pieces.Length;
        PhysicalPathKind finalKind = PhysicalPathKind.Directory;
        for (int index = 0; index < pieces.Length; index++)
        {
            current = current == "/" ? "/" + pieces[index] : current + "/" + pieces[index];
            PhysicalPathKind kind = operations.Classify(current);
            if (kind == PhysicalPathKind.Missing) { missingStart = index; break; }
            if (kind == PhysicalPathKind.Symlink || kind == PhysicalPathKind.Other || (kind == PhysicalPathKind.File && index + 1 < pieces.Length)) throw new IOException("existing path component is not a directory");
            finalKind = kind;
        }
        string existing = missingStart == pieces.Length ? current : (missingStart == 0 ? "/" : Build(pieces, missingStart));
        string canonicalExisting = operations.RealPath(existing);
        if (String.IsNullOrEmpty(canonicalExisting)) throw new IOException("realpath returned empty path");
        string[] suffix = new string[pieces.Length - missingStart];
        for (int index = 0; index < suffix.Length; index++) suffix[index] = pieces[missingStart + index];
        string canonical = canonicalExisting;
        for (int index = 0; index < suffix.Length; index++) canonical = canonical == "/" ? "/" + suffix[index] : canonical + "/" + suffix[index];
        return new ScanResult { Identity = new PhysicalPathIdentity(canonical, suffix.Length == 0, canonicalExisting, suffix), FinalKind = suffix.Length == 0 ? finalKind : PhysicalPathKind.Missing };
    }
    private static string Build(string[] pieces, int count) { string value = ""; for (int index = 0; index < count; index++) value += "/" + pieces[index]; return value.Length == 0 ? "/" : value; }
    private static void ValidateLexical(string requested)
    { if (String.IsNullOrEmpty(requested) || requested[0] != '/' || requested.IndexOf('\0') >= 0 || (requested.Length > 1 && requested[requested.Length - 1] == '/') || Path.GetFullPath(requested) != requested) throw new IOException("path spelling is not canonical"); if (requested != "/") { string[] pieces = requested.Substring(1).Split('/'); for (int index = 0; index < pieces.Length; index++) if (pieces[index].Length == 0 || pieces[index] == "." || pieces[index] == "..") throw new IOException("invalid path component"); } }
    private static bool Same(ScanResult left, ScanResult right) { PhysicalPathIdentity a = left.Identity; PhysicalPathIdentity b = right.Identity; if (left.FinalKind != right.FinalKind || a.CanonicalPath != b.CanonicalPath || a.Exists != b.Exists || a.ExistingAncestor != b.ExistingAncestor || a.MissingComponents.Length != b.MissingComponents.Length) return false; for (int index = 0; index < a.MissingComponents.Length; index++) if (a.MissingComponents[index] != b.MissingComponents[index]) return false; return true; }
    private static OracleConfigurationException Failure(Exception error) { return new OracleConfigurationException("invalid_path", error); }
}
internal sealed class PhysicalConfigurationPathResolver : IConfigurationPathResolver
{
    internal static readonly PhysicalConfigurationPathResolver Instance = new PhysicalConfigurationPathResolver();
    private PhysicalConfigurationPathResolver() { }
    public string ResolveExistingDirectory(string requested) { return PhysicalPath.ResolveExistingDirectory(requested); }
    public string ResolveExistingFile(string requested) { return PhysicalPath.ResolveExistingFile(requested); }
    public bool Contains(string parent, string candidate) { return PhysicalPath.Contains(parent, candidate); }
}
internal sealed class MacPhysicalPathOperations : IPhysicalPathOperations
{
    internal static readonly MacPhysicalPathOperations Instance = new MacPhysicalPathOperations();
    private const int PathMax = 1024; private const int EInval = 22; private const int ENoEnt = 2;
    private MacPhysicalPathOperations() { }
    [DllImport("libc", SetLastError = true)] private static extern int lstat(string path, out MacStat stat);
    [DllImport("libc", SetLastError = true)] private static extern int readlink(string path, byte[] buffer, IntPtr count);
    [DllImport("libc", SetLastError = true)] private static extern IntPtr realpath(string path, byte[] buffer);
    [StructLayout(LayoutKind.Explicit, Size = 144)]
    private struct MacStat
    {
        [FieldOffset(4)] internal ushort Mode;
    }
    public PhysicalPathKind Classify(string absolutePath)
    {
        byte[] link = new byte[PathMax]; int linked = readlink(absolutePath, link, (IntPtr)(PathMax - 1));
        if (linked >= 0) return PhysicalPathKind.Symlink;
        int linkError = Marshal.GetLastWin32Error(); if (linkError != EInval && linkError != ENoEnt) throw new IOException("readlink failed: " + linkError.ToString());
        MacStat stat; if (lstat(absolutePath, out stat) != 0) { int error = Marshal.GetLastWin32Error(); if (error == ENoEnt) return PhysicalPathKind.Missing; throw new IOException("lstat failed: " + error.ToString()); }
        int kind = stat.Mode & 61440; if (kind == 16384) return PhysicalPathKind.Directory; if (kind == 32768) return PhysicalPathKind.File; if (kind == 40960) return PhysicalPathKind.Symlink; return PhysicalPathKind.Other;
    }
    public string RealPath(string existingPath)
    { byte[] buffer = new byte[PathMax]; IntPtr result = realpath(existingPath, buffer); if (result == IntPtr.Zero) throw new IOException("realpath failed: " + Marshal.GetLastWin32Error().ToString()); int length = 0; while (length < buffer.Length && buffer[length] != 0) length++; if (length == buffer.Length) throw new IOException("realpath result too long"); return new UTF8Encoding(false, true).GetString(buffer, 0, length); }
}
