using System;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.InteropServices;

internal static class PhysicalPathTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("path", "containment uses component boundary", ContainmentUsesComponentBoundary);
        tests.Add("path", "existing paths resolve canonically", ExistingPathsResolveCanonically);
        tests.Add("path", "missing suffix is preserved", MissingSuffixIsPreserved);
        tests.Add("path", "lexical paths are strict", LexicalPathsAreStrict);
        tests.Add("path", "symlink and nondirectory are rejected", SymlinkAndNondirectoryAreRejected);
        tests.Add("path", "two scan drift is rejected", TwoScanDriftIsRejected);
    }
    private static void ContainmentUsesComponentBoundary()
    {
        Check.True(PhysicalPath.Contains("/a", "/a"), "equal");
        Check.True(PhysicalPath.Contains("/a", "/a/b"), "child");
        Check.False(PhysicalPath.Contains("/a", "/ab"), "sibling");
        Check.False(PhysicalPath.Contains("/a", "/b"), "unrelated");
        Check.True(PhysicalPath.Contains("/", "/b"), "root");
    }
    private static void ExistingPathsResolveCanonically()
    {
        FakePhysicalPathOperations ops = Base(); ops.Kinds["/a"] = PhysicalPathKind.Directory; ops.Real["/"] = "/canonical"; ops.Real["/a"] = "/canonical/a";
        PhysicalPathIdentity root = PhysicalPath.ResolvePossiblyAbsent("/", ops, null);
        PhysicalPathIdentity nested = PhysicalPath.ResolvePossiblyAbsent("/a", ops, null);
        Check.Equal("/canonical", root.CanonicalPath, "root canonical");
        Check.Equal("/canonical/a", nested.CanonicalPath, "nested canonical");
        Check.Equal("/canonical/a", nested.ExistingAncestor, "nested ancestor");
        Check.Equal(0, nested.MissingComponents.Length, "existing missing suffix");
    }
    private static void MissingSuffixIsPreserved()
    {
        FakePhysicalPathOperations ops = Base(); ops.Kinds["/a"] = PhysicalPathKind.Directory; ops.Real["/a"] = "/real/a";
        PhysicalPathIdentity one = PhysicalPath.ResolvePossiblyAbsent("/a/new", ops, null);
        PhysicalPathIdentity many = PhysicalPath.ResolvePossiblyAbsent("/a/new/deep", ops, null);
        Check.Equal("/real/a/new", one.CanonicalPath, "one suffix canonical");
        Check.Sequence(new string[] { "new", "deep" }, many.MissingComponents, "suffix order");
        Check.Equal("/real/a/new/deep", many.CanonicalPath, "many suffix canonical");
    }
    private static void LexicalPathsAreStrict()
    {
        string[] invalid = new string[] { "relative", "", "/a\0b", "/a/./b", "/a/../b", "/a//b", "/a/" };
        for (int index = 0; index < invalid.Length; index++)
        {
            FakePhysicalPathOperations ops = Base();
            OracleConfigurationException error = Check.Throws<OracleConfigurationException>(delegate { PhysicalPath.ResolvePossiblyAbsent(invalid[index], ops, null); }, "lexical failure");
            Check.Equal("invalid_path", error.Code, "lexical code"); Check.Equal(0, ops.ClassifyCalls, "no native call");
        }
    }
    private static void SymlinkAndNondirectoryAreRejected()
    {
        Type stat = typeof(MacPhysicalPathOperations).GetNestedType(
            "MacStat", BindingFlags.NonPublic);
        Check.Equal(144, Marshal.SizeOf(stat), "Darwin stat ABI size");
        AssertInvalid("/a", PhysicalPathKind.Symlink); AssertInvalid("/a", PhysicalPathKind.Other);
        AssertInvalid("/a/b", PhysicalPathKind.File);
        FakePhysicalPathOperations finalFile = Base(); finalFile.Kinds["/a"] = PhysicalPathKind.File;
        PhysicalPathIdentity file = PhysicalPath.ResolvePossiblyAbsent("/a", finalFile, null);
        Check.True(file.Exists, "final file exists");
        OracleConfigurationException fileError = Check.Throws<OracleConfigurationException>(delegate { PhysicalPath.ResolveExistingDirectory("/a", finalFile, null); }, "final file is not a directory");
        Check.Equal("invalid_path", fileError.Code, "final file directory code");
        FakePhysicalPathOperations missing = Base(); missing.Kinds["/a"] = PhysicalPathKind.Missing;
        OracleConfigurationException error = Check.Throws<OracleConfigurationException>(delegate { PhysicalPath.ResolveExistingDirectory("/a", missing, null); }, "missing directory");
        Check.Equal("invalid_path", error.Code, "missing code");
    }
    private static void TwoScanDriftIsRejected()
    {
        string[] drift = new string[] { "kind", "symlink", "canonical", "suffix", "target" };
        for (int index = 0; index < drift.Length; index++)
        {
            FakePhysicalPathOperations ops = Base(); ops.Kinds["/a"] = PhysicalPathKind.Directory; ops.Real["/a"] = "/real/a";
            int called = 0;
            OracleConfigurationException error = Check.Throws<OracleConfigurationException>(delegate {
                PhysicalPath.ResolvePossiblyAbsent("/a/b", ops, delegate {
                    called++; if (drift[index] == "kind") ops.Kinds["/a"] = PhysicalPathKind.File;
                    else if (drift[index] == "symlink") ops.Kinds["/a"] = PhysicalPathKind.Symlink;
                    else if (drift[index] == "canonical") ops.Real["/a"] = "/changed/a";
                    else if (drift[index] == "suffix") ops.Kinds["/a/b"] = PhysicalPathKind.Directory;
                    else ops.Kinds["/a/b"] = PhysicalPathKind.Directory;
                }); }, "drift failure");
            Check.Equal("invalid_path", error.Code, "drift code"); Check.Equal(1, called, "callback once");
        }
    }
    private static void AssertInvalid(string path, PhysicalPathKind kind)
    {
        FakePhysicalPathOperations ops = Base(); ops.Kinds["/a"] = kind;
        OracleConfigurationException error = Check.Throws<OracleConfigurationException>(delegate { PhysicalPath.ResolvePossiblyAbsent(path, ops, null); }, "unsafe path");
        Check.Equal("invalid_path", error.Code, "unsafe code");
    }
    private static FakePhysicalPathOperations Base()
    { FakePhysicalPathOperations ops = new FakePhysicalPathOperations(); ops.Kinds["/"] = PhysicalPathKind.Directory; ops.Real["/"] = "/"; return ops; }
}

internal sealed class FakePhysicalPathOperations : IPhysicalPathOperations
{
    internal readonly Dictionary<string, PhysicalPathKind> Kinds = new Dictionary<string, PhysicalPathKind>(StringComparer.Ordinal);
    internal readonly Dictionary<string, string> Real = new Dictionary<string, string>(StringComparer.Ordinal);
    internal int ClassifyCalls;
    public PhysicalPathKind Classify(string absolutePath) { ClassifyCalls++; PhysicalPathKind result; return Kinds.TryGetValue(absolutePath, out result) ? result : PhysicalPathKind.Missing; }
    public string RealPath(string existingPath) { string result; return Real.TryGetValue(existingPath, out result) ? result : existingPath; }
}
