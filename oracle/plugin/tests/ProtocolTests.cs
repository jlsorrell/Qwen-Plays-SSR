using System;
using System.Collections.Generic;

internal static class ProtocolTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("protocol", "registry manifest is exact", RegistryManifestIsExact);
        tests.Add("protocol", "closed error tables", ClosedErrorTables);
        tests.Add("protocol", "record constructor boundaries", RecordBoundaries);
        tests.Add("protocol", "capture value equality", CaptureValueEquality);
        tests.Add("protocol", "run mode relations are exact", RunModeRelationsAreExact);
        tests.Add("protocol", "dynamic driver count is bound to run", DynamicCountIsBoundToRun);
    }

    private static void ClosedErrorTables()
    {
        string[,] pairs = new string[,]
        {
            { "patch_install_failed", "observation patch installation failed" },
            { "input_before_initial", "manual input arrived before initial capture" },
            { "overlapping_input", "manual input arrived while settling" },
            { "unexpected_input", "native input was outside the passive vocabulary" },
            { "unscoped_process_input", "manual-looking input occurred outside the native poll scope" },
            { "hook_order_mismatch", "observation hook order mismatch" },
            { "game_method_exception", "observed game method threw" },
            { "observer_exception", "passive observer failed" },
            { "capture_failed", "game-state capture failed" },
            { "record_too_large", "encoded trace record exceeded its limit" },
            { "initial_settle_timeout", "initial capture did not settle" },
            { "settle_timeout", "input did not settle" },
            { "state_replaced", "game state identity changed" },
            { "save_path_changed", "isolated save path changed" },
            { "initial_state_mismatch", "initial replay state did not match the configured signature" },
            { "replay_alignment_failed", "replay input did not traverse the native call path" }
        };
        for (int index = 0; index < pairs.GetLength(0); index++)
        {
            OracleError error = OracleErrors.ForCode(pairs[index, 0]);
            Check.Equal(pairs[index, 0], error.Code, "record code " + index);
            Check.Equal(pairs[index, 1], error.Message, "record message " + index);
            Check.True(OracleErrors.IsRecordCode(pairs[index, 0]), "record membership");
            Check.False(OracleMarkerErrors.IsMarkerOnly(pairs[index, 0]), "record not marker");
        }
        string[] markers = new string[]
        {
            "invalid_mode", "invalid_configuration", "invalid_assembly",
            "invalid_reflection", "invalid_path", "trace_exists",
            "save_redirect_failed", "trace_io_failed"
        };
        for (int index = 0; index < markers.Length; index++)
        {
            Check.True(OracleMarkerErrors.IsMarkerOnly(markers[index]), "marker " + index);
            Check.False(OracleErrors.IsRecordCode(markers[index]), "marker not record");
            string marker = markers[index];
            Check.Throws<ArgumentException>(
                delegate { OracleErrors.ForCode(marker); }, "marker rejected by record table");
        }
        Check.Throws<ArgumentException>(
            delegate { OracleErrors.ForCode("unknown"); }, "unknown record code");
    }

    private static CaptureRecord Capture(string rawSave, string identity)
    {
        return new CaptureRecord(
            rawSave, identity, "", false, false, false, false, "", "",
            0, 0, 0);
    }

    private static void RecordBoundaries()
    {
        string runId = "0123456789abcdef0123456789abcdef";
        DateTime utc = new DateTime(2026, 7, 31, 19, 9, 50, DateTimeKind.Utc);
        CaptureRecord capture = Capture("save", "-2147483648");
        new RunRecord(runId, OracleProtocol.ExpectedAssemblySha256, utc);
        new StepRecord(runId, Int32.MaxValue, OracleInput.Undo, true, false, 2, false, capture);
        new StepRecord(runId, 0, OracleInput.North, false, false, 600, false, capture);
        new ErrorRecord(runId, null, null, "capture_failed", 0, null);
        new ErrorRecord(runId, Int32.MaxValue, OracleInput.East, "settle_timeout", 600, capture);
        Check.Throws<ArgumentException>(
            delegate { new RunRecord(runId.ToUpperInvariant(), OracleProtocol.ExpectedAssemblySha256, utc); },
            "uppercase run ID");
        Check.Throws<ArgumentException>(
            delegate { new RunRecord(runId, OracleProtocol.ExpectedAssemblySha256, utc.ToLocalTime()); },
            "non-UTC start");
        Check.Throws<ArgumentException>(
            delegate { Capture("save", "-0"); }, "negative zero identity");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate { new StepRecord(runId, 0, OracleInput.North, true, false, 1, false, capture); },
            "step frame one");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate { new StepRecord(runId, 0, OracleInput.North, true, false, 601, false, capture); },
            "step frame 601");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate { new ErrorRecord(runId, null, null, "capture_failed", -1, null); },
            "error frame negative");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate { new ErrorRecord(runId, null, null, "capture_failed", 601, null); },
            "error frame 601");
        Check.Throws<ArgumentException>(
            delegate { new StepRecord(runId, 0, OracleInput.North, true, false, 2, true, capture); },
            "state replacement step");
        Check.Throws<ArgumentException>(
            delegate { new ErrorRecord(runId, 0, null, "capture_failed", 0, null); },
            "mismatched nullable input fields");
        ErrorRecord unexpected = new ErrorRecord(
            runId, 0, null, "unexpected_input", 0, null);
        Check.Equal(0, unexpected.InputIndex.Value,
            "unknown native input retains the next input index");
        Check.False(unexpected.Input.HasValue,
            "unknown native input is not fabricated as a schema input");
        Check.Throws<ArgumentException>(
            delegate
            {
                new ErrorRecord(
                    runId, null, OracleInput.North,
                    "unexpected_input", 0, null);
            },
            "input never appears without an input index");
    }

    private static void CaptureValueEquality()
    {
        CaptureRecord left = Capture("save", "17");
        CaptureRecord equal = Capture("save", "17");
        CaptureRecord different = Capture("changed", "17");
        Check.True(left.Equals(equal), "complete capture equality");
        Check.Equal(left.GetHashCode(), equal.GetHashCode(), "equal hash codes");
        Check.False(left.Equals(different), "raw-save inequality");
        Check.False(left.Equals(null), "null inequality");
    }

    private static void RunModeRelationsAreExact()
    {
        DateTime utc = new DateTime(
            2026, 7, 31, 19, 9, 50, DateTimeKind.Utc).AddTicks(3199100);
        RunRecord legacyPassive = new RunRecord(
            ProtocolSamples.RunId, OracleProtocol.ExpectedAssemblySha256, utc);
        RunRecord explicitPassive = new RunRecord(
            ProtocolSamples.RunId, OracleMode.Passive,
            OracleProtocol.ExpectedAssemblySha256, null,
            OracleProtocol.ExpectedInputCount, utc);
        Check.Bytes(
            CanonicalJson.EncodeRun(legacyPassive),
            CanonicalJson.EncodeRun(explicitPassive),
            "passive overload bytes remain identical");
        Check.Equal(OracleMode.Passive, legacyPassive.Mode, "legacy mode");
        Check.Equal(
            OracleProtocol.ExpectedInputCount,
            legacyPassive.ExpectedInputCount,
            "legacy passive count");
        Check.True(legacyPassive.InputSha256 == null, "legacy passive hash");

        RunRecord replay = ProtocolSamples.ReplayRun;
        Check.Equal(OracleMode.Replay, replay.Mode, "replay mode");
        Check.Equal(ProtocolSamples.ReplayInputSha256, replay.InputSha256,
            "replay hash");
        Check.Equal(1, replay.ExpectedInputCount, "replay count");
        Check.Equal(1, ProtocolSamples.ReplayEnd.InputCount, "replay End count");

        Check.Throws<ArgumentOutOfRangeException>(
            delegate
            {
                new RunRecord(
                    ProtocolSamples.RunId, OracleMode.Off,
                    OracleProtocol.ExpectedAssemblySha256, null, 1, utc);
            },
            "off Run mode");
        Check.Throws<ArgumentNullException>(
            delegate
            {
                new RunRecord(
                    ProtocolSamples.RunId, OracleMode.Replay,
                    OracleProtocol.ExpectedAssemblySha256, null, 1, utc);
            },
            "replay null hash");
        Check.Throws<ArgumentException>(
            delegate
            {
                new RunRecord(
                    ProtocolSamples.RunId, OracleMode.Replay,
                    OracleProtocol.ExpectedAssemblySha256,
                    ProtocolSamples.ReplayInputSha256.ToUpperInvariant(), 1, utc);
            },
            "replay uppercase hash");
        Check.Throws<ArgumentException>(
            delegate
            {
                new RunRecord(
                    ProtocolSamples.RunId, OracleMode.Replay,
                    OracleProtocol.ExpectedAssemblySha256,
                    ProtocolSamples.ReplayInputSha256.Substring(1), 1, utc);
            },
            "replay short hash");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate
            {
                new RunRecord(
                    ProtocolSamples.RunId, OracleMode.Replay,
                    OracleProtocol.ExpectedAssemblySha256,
                    ProtocolSamples.ReplayInputSha256, 0, utc);
            },
            "replay zero count");
        Check.Throws<ArgumentException>(
            delegate
            {
                new RunRecord(
                    ProtocolSamples.RunId, OracleMode.Passive,
                    OracleProtocol.ExpectedAssemblySha256,
                    ProtocolSamples.ReplayInputSha256,
                    OracleProtocol.ExpectedInputCount, utc);
            },
            "passive non-null hash");
        Check.Throws<ArgumentException>(
            delegate
            {
                new RunRecord(
                    ProtocolSamples.RunId, OracleMode.Passive,
                    OracleProtocol.ExpectedAssemblySha256, null, 2, utc);
            },
            "passive non-three count");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate
            {
                new EndRecord(ProtocolSamples.RunId, 0, utc);
            },
            "zero End count");
    }

    private static void DynamicCountIsBoundToRun()
    {
        IList<string> compatibleEvents = new List<string>();
        FakeTraceSink compatibleSink = new FakeTraceSink(compatibleEvents);
        PassiveDriver compatible = new PassiveDriver(
            compatibleSink,
            new FakePassiveReporter(compatibleEvents),
            1,
            OracleProtocol.MaxSettleFrames,
            OracleProtocol.MaxSettleSeconds);
        Check.True(compatible.Prepare(ProtocolSamples.ReplayRun),
            "replay count one prepares");
        Check.True(compatible.Activate(), "replay count one activates");
        Check.Equal(1, compatibleSink.RunCalls, "replay Run reaches sink once");

        IList<string> mismatchEvents = new List<string>();
        FakeTraceSink mismatchSink = new FakeTraceSink(mismatchEvents);
        PassiveDriver mismatch = new PassiveDriver(
            mismatchSink,
            new FakePassiveReporter(mismatchEvents),
            2,
            OracleProtocol.MaxSettleFrames,
            OracleProtocol.MaxSettleSeconds);
        ArgumentException mismatchError = Check.Throws<ArgumentException>(
            delegate { mismatch.Prepare(ProtocolSamples.ReplayRun); },
            "mismatched replay count rejects before Run write");
        Check.Equal(
            "Run expected_input_count does not match driver",
            mismatchError.Message,
            "mismatched replay count message");
        Check.Equal(0, mismatchSink.RunCalls,
            "mismatched replay count makes zero sink calls");
        RunRecord matchingCount = new RunRecord(
            ProtocolSamples.RunId, OracleMode.Replay,
            OracleProtocol.ExpectedAssemblySha256,
            ProtocolSamples.ReplayInputSha256, 2,
            ProtocolSamples.ReplayRun.StartedAtUtc);
        Check.True(mismatch.Prepare(matchingCount),
            "mismatch leaves Prepare available for matching Run");
        Check.Equal(1, mismatchSink.RunCalls,
            "matching replay Run reaches sink once after mismatch");
        Check.Same(matchingCount, mismatchSink.RunRecords[0],
            "matching replay Run is retained after mismatch");

        Check.Throws<ArgumentOutOfRangeException>(
            delegate
            {
                new PassiveDriver(
                    new FakeTraceSink(new List<string>()),
                    new FakePassiveReporter(new List<string>()),
                    0,
                    OracleProtocol.MaxSettleFrames,
                    OracleProtocol.MaxSettleSeconds);
            },
            "zero expected count rejected");

        IList<string> passiveEvents = new List<string>();
        FakeTraceSink passiveSink = new FakeTraceSink(passiveEvents);
        PassiveDriver passive = new PassiveDriver(
            passiveSink,
            new FakePassiveReporter(passiveEvents),
            OracleProtocol.ExpectedInputCount,
            OracleProtocol.MaxSettleFrames,
            OracleProtocol.MaxSettleSeconds);
        Check.True(passive.Prepare(ProtocolSamples.Run), "passive still prepares");
        Check.Equal(
            OracleProtocol.ExpectedInputCount,
            passiveSink.RunRecords[0].ExpectedInputCount,
            "passive still receives exactly three inputs");

        DriverFixture ready = DriverFixture.Ready();
        IReplayDriver replayDriver = (IReplayDriver)ready.Driver;
        Check.True(replayDriver.IsReadyForReplay(ready.State, 0),
            "durable ready state and count are replay-ready");
        Check.False(replayDriver.IsReadyForReplay(ready.OtherState, 0),
            "different durable state is not replay-ready");
        Check.False(replayDriver.IsReadyForReplay(ready.State, 1),
            "different durable count is not replay-ready");
        HookToken stateSet = ready.Driver.StateSetEntered(
            ready.State, ready.State);
        Check.True(stateSet.Active, "same-state StateSet context opens");
        Check.False(replayDriver.IsReadyForReplay(ready.State, 0),
            "unresolved StateSet is not replay-ready");
        ready.Driver.StateSetReturned(stateSet, ready.State, 4.0);
        Check.True(replayDriver.IsReadyForReplay(ready.State, 0),
            "matching StateSet return restores replay readiness");
    }

    private static void RegistryManifestIsExact()
    {
        TestRegistry registry = new TestRegistry();
        registry.Add("protocol", "registry manifest is exact", delegate { });
        registry.VerifyManifest(
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 }
            });
        Check.Throws<InvalidOperationException>(
            delegate
            {
                registry.Add(
                    "protocol", "registry manifest is exact", delegate { });
            },
            "duplicate test identity");

        TestRegistry renamed = new TestRegistry();
        renamed.Add("protocol", "registry manifest was renamed", delegate { });
        bool renameRejected = RejectsManifest(
            renamed,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 }
            });

        TestRegistry swapped = new TestRegistry();
        swapped.Add("encoding", "registry manifest is exact", delegate { });
        swapped.Add("protocol", "golden fixture bytes", delegate { });
        bool swapRejected = RejectsManifest(
            swapped,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 },
                { "encoding", 1 }
            });

        TestRegistry reordered = new TestRegistry();
        reordered.Add("protocol", "closed error tables", delegate { });
        reordered.Add("protocol", "registry manifest is exact", delegate { });
        bool reorderRejected = RejectsManifest(
            reordered,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 2 }
            });

        TestRegistry unknown = new TestRegistry();
        unknown.Add("sample", "one", delegate { });
        bool unknownRejected = RejectsManifest(
            unknown,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "sample", 1 }
            });

        bool negativeRejected = RejectsManifest(
            registry,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", -1 }
            });
        bool overfullRejected = RejectsManifest(
            registry,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 7 }
            });

        bool missingRejected = RejectsManifest(
            registry,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 2 }
            });

        TestRegistry extra = new TestRegistry();
        extra.Add("protocol", "registry manifest is exact", delegate { });
        extra.Add("encoding", "golden fixture bytes", delegate { });
        bool extraRejected = RejectsManifest(
            extra,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 }
            });

        TestRegistry slashPairs = new TestRegistry();
        bool slashPairsDistinct = true;
        try
        {
            slashPairs.Add("a/b", "c", delegate { });
            slashPairs.Add("a", "b/c", delegate { });
        }
        catch (InvalidOperationException)
        {
            slashPairsDistinct = false;
        }

        Check.True(renameRejected, "same-count rename was accepted");
        Check.True(swapRejected, "balanced cohort swap was accepted");
        Check.True(reorderRejected, "registration reorder was accepted");
        Check.True(unknownRejected, "unknown manifest cohort was accepted");
        Check.True(negativeRejected, "negative manifest count was accepted");
        Check.True(overfullRejected, "overfull manifest count was accepted");
        Check.True(missingRejected, "missing registration was accepted");
        Check.True(extraRejected, "extra registration was accepted");
        Check.True(slashPairsDistinct, "structural identities were aliased");
    }

    private static bool RejectsManifest(
        TestRegistry registry,
        IDictionary<string, int> expected)
    {
        try
        {
            registry.VerifyManifest(expected);
            return false;
        }
        catch (InvalidOperationException)
        {
            return true;
        }
    }
}
