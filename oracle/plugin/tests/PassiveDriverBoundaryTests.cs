using System;
using System.Reflection;
using System.Threading;

internal sealed class EqualOwner
{
    private readonly int value;

    internal EqualOwner(int value)
    {
        this.value = value;
    }

    public override bool Equals(object other)
    {
        EqualOwner equal = other as EqualOwner;
        return equal != null && value == equal.value;
    }

    public override int GetHashCode()
    {
        return value;
    }
}

internal sealed class BoundaryFakePassiveReporter : IPassiveReporter
{
    internal int ReadyCalls;
    internal int CompletedInputs;
    internal int CompleteCalls;
    internal int FailedCalls;
    internal string FailedCode;
    internal int DiagnosticCalls;
    internal string DiagnosticMessage;

    public void Ready(int completedInputs)
    {
        ReadyCalls++;
        CompletedInputs = completedInputs;
    }

    public void Complete()
    {
        CompleteCalls++;
    }

    public void Failed(string code)
    {
        FailedCalls++;
        FailedCode = code;
    }

    public void Diagnostic(string message)
    {
        DiagnosticCalls++;
        DiagnosticMessage = message;
    }
}

internal static class PassiveDriverBoundaryTests
{
    private const int WorkerTimeoutMilliseconds = 5000;

    private static IPassiveReporter CompileBoundarySurface(
        CaptureException captureException,
        HookKind hookKind,
        HookToken hookToken,
        UpdateDirective updateDirective,
        GateSampleKind gateSampleKind,
        GateSample gateSample,
        IPassiveReporter reporter)
    {
        return reporter;
    }

    private sealed class HookSnapshot
    {
        internal object Owner;
        internal long Id;
        internal HookKind Kind;
        internal bool Active;
        internal bool BelongsToOwner;
    }

    private sealed class DirectiveSnapshot
    {
        internal object Owner;
        internal long Id;
        internal long Epoch;
        internal int SettleFrames;
        internal double NowSeconds;
        internal bool Active;
        internal bool InspectGate;
        internal bool TimeoutAfterSample;
        internal bool BelongsToOwner;
    }

    internal static void Register(TestRegistry tests)
    {
        tests.Add(
            "driver-boundary",
            "hook token is owner bound and single consume",
            HookTokenIsOwnerBoundAndSingleConsume);
        tests.Add(
            "driver-boundary",
            "update directive authorizes rebases and consumes once",
            UpdateDirectiveAuthorizesRebasesAndConsumesOnce);
    }

    private static void HookTokenIsOwnerBoundAndSingleConsume()
    {
        AssertCaptureExceptionContract();
        AssertHookKindContract();
        AssertHookFactoryValidationAndShapes();
        AssertSequentialHookConsumption();
        AssertConcurrentHookConsumption();
    }

    private static void AssertCaptureExceptionContract()
    {
        Type type = typeof(CaptureException);
        AssertGlobalInternalSealed(type, "CaptureException");
        Check.True(
            typeof(Exception).IsAssignableFrom(type),
            "CaptureException derives from Exception");

        ConstructorInfo[] constructors = type.GetConstructors(
            BindingFlags.Instance
            | BindingFlags.Public
            | BindingFlags.NonPublic
            | BindingFlags.DeclaredOnly);
        Check.Equal(2, constructors.Length, "CaptureException constructor count");
        ConstructorInfo plainConstructor = type.GetConstructor(
            BindingFlags.Instance | BindingFlags.NonPublic,
            null,
            new Type[] { typeof(string) },
            null);
        ConstructorInfo wrappedConstructor = type.GetConstructor(
            BindingFlags.Instance | BindingFlags.NonPublic,
            null,
            new Type[] { typeof(string), typeof(Exception) },
            null);
        Check.True(
            plainConstructor != null && plainConstructor.IsAssembly,
            "CaptureException message constructor is internal");
        Check.True(
            wrappedConstructor != null && wrappedConstructor.IsAssembly,
            "CaptureException wrapping constructor is internal");

        CaptureException plain = new CaptureException("plain");
        Check.Equal("plain", plain.Message, "plain capture message");
        Check.True(
            plain.InnerException == null,
            "plain capture has no inner exception");

        InvalidOperationException inner =
            new InvalidOperationException("inner");
        CaptureException wrapped = new CaptureException("wrapped", inner);
        Check.Equal("wrapped", wrapped.Message, "wrapped capture message");
        Check.Same(inner, wrapped.InnerException, "wrapped capture inner identity");
    }

    private static void AssertHookKindContract()
    {
        AssertGlobalInternalEnum(typeof(HookKind), "HookKind");
        string[] names = new string[]
        {
            "PlayerPoll", "ProcessInput", "Undo", "Restart", "StateSet"
        };
        Check.Sequence(
            names,
            Enum.GetNames(typeof(HookKind)),
            "hook kind names");
        int[] actualValues = new int[names.Length];
        for (int index = 0; index < names.Length; index++)
        {
            actualValues[index] = (int)Enum.Parse(
                typeof(HookKind), names[index], false);
        }
        Check.Sequence(
            new int[] { 0, 1, 2, 3, 4 },
            actualValues,
            "hook kind numeric values");
    }

    private static void AssertHookFactoryValidationAndShapes()
    {
        AssertGlobalInternalSealed(typeof(HookToken), "HookToken");
        object owner = new object();
        AssertArgumentNull(
            "owner",
            delegate { HookToken.Issued(null, 1L, HookKind.PlayerPoll); },
            "issued hook rejects null owner");
        AssertArgumentOutOfRange(
            "id",
            delegate { HookToken.Issued(owner, 0L, HookKind.PlayerPoll); },
            "issued hook rejects zero ID");
        AssertArgumentOutOfRange(
            "id",
            delegate { HookToken.Issued(owner, -1L, HookKind.PlayerPoll); },
            "issued hook rejects negative ID");
        AssertArgumentOutOfRange(
            "kind",
            delegate { HookToken.Issued(owner, 1L, (HookKind)(-1)); },
            "issued hook rejects negative kind");
        AssertArgumentOutOfRange(
            "kind",
            delegate { HookToken.Issued(owner, 1L, (HookKind)5); },
            "issued hook rejects upper kind");
        AssertArgumentOutOfRange(
            "kind",
            delegate { HookToken.Inert((HookKind)(-1)); },
            "inert hook rejects negative kind");
        AssertArgumentOutOfRange(
            "kind",
            delegate { HookToken.Inert((HookKind)5); },
            "inert hook rejects upper kind");

        HookKind[] kinds = new HookKind[]
        {
            HookKind.PlayerPoll,
            HookKind.ProcessInput,
            HookKind.Undo,
            HookKind.Restart,
            HookKind.StateSet
        };
        for (int index = 0; index < kinds.Length; index++)
        {
            string label = "hook kind " + kinds[index].ToString();
            object issuedOwner = new object();
            HookToken issued = HookToken.Issued(
                issuedOwner, (long)index + 1L, kinds[index]);
            Check.True(issued.Active, label + " issued active");
            Check.Equal(
                (long)index + 1L,
                issued.Id,
                label + " issued ID");
            Check.Equal(kinds[index], issued.Kind, label + " issued kind");
            Check.True(
                issued.BelongsTo(issuedOwner),
                label + " issued owner identity");
            Check.False(
                issued.BelongsTo(new object()),
                label + " issued rejects foreign owner");
            Check.False(
                issued.BelongsTo(null),
                label + " issued rejects null owner");

            HookToken inert = HookToken.Inert(kinds[index]);
            Check.False(inert.Active, label + " inert inactive");
            Check.Equal(0L, inert.Id, label + " inert zero ID");
            Check.Equal(kinds[index], inert.Kind, label + " inert kind");
            Check.False(
                inert.BelongsTo(null),
                "inert token rejects null owner");
            Check.False(
                inert.BelongsTo(issuedOwner),
                label + " inert rejects nonnull owner");
            Check.False(inert.TryConsume(), label + " inert cannot consume");
            Check.False(
                inert.TryConsume(),
                label + " inert retry cannot consume");
            Check.False(inert.Active, label + " inert remains inactive");
            Check.Equal(0L, inert.Id, label + " inert ID remains zero");
            Check.Equal(
                kinds[index],
                inert.Kind,
                label + " inert kind remains stable");
        }

        EqualOwner equalOwner = new EqualOwner(17);
        EqualOwner equalForeign = new EqualOwner(17);
        Check.True(equalOwner.Equals(equalForeign), "hook owners compare equal");
        HookToken identity = HookToken.Issued(
            equalOwner, 17L, HookKind.StateSet);
        Check.True(
            identity.BelongsTo(equalOwner),
            "hook accepts identical owner reference");
        Check.False(
            identity.BelongsTo(equalForeign),
            "hook rejects equal-looking owner");
        HookToken maximum = HookToken.Issued(
            owner, Int64.MaxValue, HookKind.PlayerPoll);
        Check.Equal(
            Int64.MaxValue,
            maximum.Id,
            "issued hook maximum ID accepted");
        Check.True(maximum.TryConsume(), "maximum hook cleanup succeeds");
    }

    private static void AssertSequentialHookConsumption()
    {
        object owner = new object();
        HookToken token = HookToken.Issued(owner, 31L, HookKind.Undo);
        HookSnapshot before = SnapshotHook(token, owner);
        Check.True(token.TryConsume(), "hook first consume succeeds");
        AssertHookSnapshot(token, before, "hook first consume metadata");
        Check.False(token.TryConsume(), "hook second consume rejected");
        AssertHookSnapshot(token, before, "hook retry metadata");
        Check.True(token.Active, "consumed hook remains active");
    }

    private static void AssertConcurrentHookConsumption()
    {
        object owner = new object();
        HookToken token = HookToken.Issued(
            owner, 7000000001L, HookKind.Restart);
        HookSnapshot before = SnapshotHook(token, owner);
        int winners = RunTwoWorkers(
            delegate { return token.TryConsume(); },
            delegate { return token.TryConsume(); },
            "hook consume race");
        Check.Equal(1, winners, "hook race exactly one winner");
        Check.False(token.TryConsume(), "hook race leaves token consumed");
        AssertHookSnapshot(token, before, "hook race metadata");
    }

    private static void UpdateDirectiveAuthorizesRebasesAndConsumesOnce()
    {
        AssertUpdateTypeShapeAndInactiveContract();
        AssertIssuedFactoryValidationAndFlagCombinations();
        AssertDirectiveTransitionMatrixAndMetadata();
        AssertDirectiveRebaseContract();
        AssertDirectiveCompetitions();
        AssertGateSampleContract();
        AssertPassiveReporterContract();
    }

    private static void AssertUpdateTypeShapeAndInactiveContract()
    {
        Type type = typeof(UpdateDirective);
        AssertGlobalInternalSealed(type, "UpdateDirective");
        Check.True(
            type.GetMethod(
                "TryConsume",
                BindingFlags.Instance
                | BindingFlags.Public
                | BindingFlags.NonPublic
                | BindingFlags.DeclaredOnly) == null,
            "update directive has no TryConsume alias");

        AssertArgumentNull(
            "owner",
            delegate { UpdateDirective.Inactive(null); },
            "inactive directive rejects null owner");
        object owner = new object();
        UpdateDirective inactive = UpdateDirective.Inactive(owner);
        Check.False(inactive.Active, "inactive directive inactive");
        Check.Equal(0L, inactive.Id, "inactive directive zero ID");
        Check.Equal(0L, inactive.Epoch, "inactive directive zero epoch");
        Check.Equal(
            0,
            inactive.SettleFrames,
            "inactive directive zero settle frames");
        Check.Equal(
            0.0,
            inactive.NowSeconds,
            "inactive directive zero time");
        Check.False(
            inactive.InspectGate,
            "inactive directive gate flag false");
        Check.False(
            inactive.TimeoutAfterSample,
            "inactive directive timeout flag false");
        Check.True(
            inactive.BelongsTo(owner),
            "inactive directive retains owner");
        Check.False(
            inactive.BelongsTo(new object()),
            "inactive directive rejects foreign owner");
        Check.False(
            inactive.BelongsTo(null),
            "inactive directive rejects null owner identity");

        DirectiveSnapshot before = SnapshotDirective(inactive, owner);
        Check.False(
            inactive.TryAuthorize(),
            "inactive directive authorization rejected");
        Check.False(
            inactive.TryComplete(),
            "inactive directive completion rejected");
        Check.False(
            inactive.TryFail(),
            "inactive directive failure rejected");
        Check.Throws<InvalidOperationException>(
            delegate { inactive.RebaseInitialEpoch(0L, 0); },
            "inactive directive rebase rejected");
        AssertDirectiveSnapshot(
            inactive,
            before,
            "inactive directive rejected transitions preserve metadata");
    }

    private static void AssertIssuedFactoryValidationAndFlagCombinations()
    {
        object owner = new object();
        AssertArgumentNull(
            "owner",
            delegate
            {
                UpdateDirective.Issued(
                    null, 1L, 0L, 0, 0.0, false, false);
            },
            "issued directive rejects null owner");
        AssertArgumentOutOfRange(
            "id",
            delegate
            {
                UpdateDirective.Issued(
                    owner, 0L, 0L, 0, 0.0, false, false);
            },
            "issued directive rejects zero ID");
        AssertArgumentOutOfRange(
            "id",
            delegate
            {
                UpdateDirective.Issued(
                    owner, -1L, 0L, 0, 0.0, false, false);
            },
            "issued directive rejects negative ID");
        AssertArgumentOutOfRange(
            "epoch",
            delegate
            {
                UpdateDirective.Issued(
                    owner, 1L, -1L, 0, 0.0, false, false);
            },
            "issued directive rejects negative epoch");
        AssertArgumentOutOfRange(
            "settleFrames",
            delegate
            {
                UpdateDirective.Issued(
                    owner, 1L, 0L, -1, 0.0, false, false);
            },
            "issued directive rejects negative settle frames");
        AssertArgumentOutOfRange(
            "nowSeconds",
            delegate
            {
                UpdateDirective.Issued(
                    owner, 1L, 0L, 0, -0.5, false, false);
            },
            "issued directive rejects negative time");
        AssertArgumentOutOfRange(
            "nowSeconds",
            delegate
            {
                UpdateDirective.Issued(
                    owner, 1L, 0L, 0, Double.NaN, false, false);
            },
            "issued directive rejects NaN time");
        AssertArgumentOutOfRange(
            "nowSeconds",
            delegate
            {
                UpdateDirective.Issued(
                    owner,
                    1L,
                    0L,
                    0,
                    Double.PositiveInfinity,
                    false,
                    false);
            },
            "issued directive rejects positive infinite time");
        AssertArgumentOutOfRange(
            "nowSeconds",
            delegate
            {
                UpdateDirective.Issued(
                    owner,
                    1L,
                    0L,
                    0,
                    Double.NegativeInfinity,
                    false,
                    false);
            },
            "issued directive rejects negative infinite time");

        UpdateDirective boundary = UpdateDirective.Issued(
            owner, 1L, 0L, 0, 0.0, false, false);
        Check.Equal(1L, boundary.Id, "issued directive minimum ID");
        Check.Equal(0L, boundary.Epoch, "issued directive zero epoch accepted");
        Check.Equal(
            0,
            boundary.SettleFrames,
            "issued directive zero frames accepted");
        Check.Equal(
            0.0,
            boundary.NowSeconds,
            "issued directive zero time accepted");
        Check.True(
            boundary.TryAuthorize(),
            "issued boundary cleanup authorization succeeds");
        Check.True(
            boundary.TryComplete(),
            "issued boundary cleanup completion succeeds");

        UpdateDirective maximum = UpdateDirective.Issued(
            owner,
            Int64.MaxValue,
            Int64.MaxValue,
            Int32.MaxValue,
            Double.MaxValue,
            true,
            true);
        Check.Equal(
            Int64.MaxValue,
            maximum.Id,
            "issued directive maximum ID accepted");
        Check.Equal(
            Int64.MaxValue,
            maximum.Epoch,
            "issued directive maximum epoch accepted");
        Check.Equal(
            Int32.MaxValue,
            maximum.SettleFrames,
            "issued directive maximum frames accepted");
        Check.Equal(
            Double.MaxValue,
            maximum.NowSeconds,
            "issued directive maximum finite time accepted");
        Check.True(
            maximum.TryAuthorize(),
            "maximum directive cleanup authorization succeeds");
        Check.True(
            maximum.TryComplete(),
            "maximum directive cleanup completion succeeds");

        bool[] flags = new bool[] { false, true };
        int combination = 0;
        for (int inspect = 0; inspect < flags.Length; inspect++)
        {
            for (int timeout = 0; timeout < flags.Length; timeout++)
            {
                combination++;
                object flagOwner = new object();
                UpdateDirective directive = UpdateDirective.Issued(
                    flagOwner,
                    100L + combination,
                    10L + combination,
                    combination,
                    0.25 * combination,
                    flags[inspect],
                    flags[timeout]);
                string label = "gate flag combination "
                    + combination.ToString();
                Check.True(directive.Active, label + " active");
                Check.Equal(
                    flags[inspect],
                    directive.InspectGate,
                    label + " inspect flag");
                Check.Equal(
                    flags[timeout],
                    directive.TimeoutAfterSample,
                    label + " timeout flag");
                DirectiveSnapshot before = SnapshotDirective(
                    directive, flagOwner);
                Check.True(
                    directive.TryAuthorize(),
                    label + " authorization succeeds");
                Check.True(
                    directive.TryComplete(),
                    label + " completion succeeds");
                AssertDirectiveSnapshot(
                    directive,
                    before,
                    label + " metadata survives completion");
            }
        }

        EqualOwner equalOwner = new EqualOwner(29);
        EqualOwner equalForeign = new EqualOwner(29);
        Check.True(
            equalOwner.Equals(equalForeign),
            "directive owners compare equal");
        UpdateDirective identity = UpdateDirective.Issued(
            equalOwner, 29L, 0L, 0, 0.0, false, true);
        Check.True(
            identity.BelongsTo(equalOwner),
            "directive accepts identical owner reference");
        Check.False(
            identity.BelongsTo(equalForeign),
            "directive rejects equal-looking owner");
        Check.False(
            identity.BelongsTo(null),
            "issued directive rejects null owner identity");
        Check.True(
            identity.TryAuthorize(),
            "identity directive cleanup authorization succeeds");
        Check.True(
            identity.TryComplete(),
            "identity directive cleanup completion succeeds");
    }

    private static void AssertDirectiveTransitionMatrixAndMetadata()
    {
        object issuedOwner = new object();
        UpdateDirective issued = UpdateDirective.Issued(
            issuedOwner, 201L, 3L, 4, 2.5, true, false);
        DirectiveSnapshot issuedBefore = SnapshotDirective(
            issued, issuedOwner);
        Check.False(issued.TryComplete(), "issued complete rejected");
        AssertDirectiveSnapshot(
            issued,
            issuedBefore,
            "issued rejected completion preserves metadata");
        Check.True(issued.TryAuthorize(), "issued authorization succeeds");
        Check.False(
            issued.TryAuthorize(),
            "authorized directive rejects reauthorization");
        Check.True(
            issued.TryFail(),
            "authorized cleanup after issued matrix succeeds");

        object issuedFailOwner = new object();
        UpdateDirective issuedFail = UpdateDirective.Issued(
            issuedFailOwner, 202L, 5L, 6, 3.5, false, true);
        DirectiveSnapshot issuedFailBefore = SnapshotDirective(
            issuedFail, issuedFailOwner);
        Check.True(issuedFail.TryFail(), "issued fail succeeds");
        Check.False(
            issuedFail.TryFail(),
            "issued failed directive rejects second failure");
        Check.False(
            issuedFail.TryAuthorize(),
            "issued failed directive rejects authorization");
        Check.False(
            issuedFail.TryComplete(),
            "issued failed directive rejects completion");
        AssertDirectiveSnapshot(
            issuedFail,
            issuedFailBefore,
            "issued failure preserves metadata");
        Check.Throws<InvalidOperationException>(
            delegate { issuedFail.RebaseInitialEpoch(6L, 7); },
            "issued failed directive rejects rebase");
        AssertDirectiveSnapshot(
            issuedFail,
            issuedFailBefore,
            "issued failure rebase rejection preserves metadata");

        object completeOwner = new object();
        UpdateDirective completed = UpdateDirective.Issued(
            completeOwner, 203L, 7L, 8, 4.5, true, true);
        Check.True(
            completed.TryAuthorize(),
            "completion path authorization succeeds");
        DirectiveSnapshot completeBefore = SnapshotDirective(
            completed, completeOwner);
        Check.True(completed.TryComplete(), "authorized complete succeeds");
        Check.False(
            completed.TryFail(),
            "completed directive fail rejected");
        Check.False(
            completed.TryComplete(),
            "completed directive second completion rejected");
        Check.False(
            completed.TryAuthorize(),
            "completed directive authorization rejected");
        AssertDirectiveSnapshot(
            completed,
            completeBefore,
            "completion preserves metadata");
        Check.Throws<InvalidOperationException>(
            delegate { completed.RebaseInitialEpoch(8L, 9); },
            "completed directive rebase rejected");
        AssertDirectiveSnapshot(
            completed,
            completeBefore,
            "completed rebase rejection preserves metadata");

        object authorizedFailOwner = new object();
        UpdateDirective authorizedFail = UpdateDirective.Issued(
            authorizedFailOwner, 204L, 9L, 10, 5.5, false, false);
        Check.True(
            authorizedFail.TryAuthorize(),
            "authorized failure path authorization succeeds");
        DirectiveSnapshot authorizedFailBefore = SnapshotDirective(
            authorizedFail, authorizedFailOwner);
        Check.True(
            authorizedFail.TryFail(),
            "authorized fail succeeds");
        Check.False(
            authorizedFail.TryFail(),
            "authorized failed directive second failure rejected");
        Check.False(
            authorizedFail.TryComplete(),
            "authorized failed directive completion rejected");
        Check.False(
            authorizedFail.TryAuthorize(),
            "authorized failed directive authorization rejected");
        AssertDirectiveSnapshot(
            authorizedFail,
            authorizedFailBefore,
            "authorized failure preserves metadata");
        Check.Throws<InvalidOperationException>(
            delegate { authorizedFail.RebaseInitialEpoch(10L, 11); },
            "authorized failed directive rejects rebase");
        AssertDirectiveSnapshot(
            authorizedFail,
            authorizedFailBefore,
            "authorized failure rebase rejection preserves metadata");
    }

    private static void AssertDirectiveRebaseContract()
    {
        object issuedOwner = new object();
        UpdateDirective issued = UpdateDirective.Issued(
            issuedOwner, 301L, 3L, 4, 2.5, true, true);
        DirectiveSnapshot issuedBefore = SnapshotDirective(
            issued, issuedOwner);
        Check.Throws<InvalidOperationException>(
            delegate { issued.RebaseInitialEpoch(4L, 1); },
            "issued rebase rejected");
        AssertDirectiveSnapshot(
            issued,
            issuedBefore,
            "issued rebase rejection preserves metadata");
        Check.True(
            issued.TryAuthorize(),
            "rebase directive authorization succeeds");

        DirectiveSnapshot beforeNegativeEpoch = SnapshotDirective(
            issued, issuedOwner);
        AssertArgumentOutOfRange(
            "replacementEpoch",
            delegate { issued.RebaseInitialEpoch(-1L, 1); },
            "negative replacement epoch");
        AssertDirectiveSnapshot(
            issued,
            beforeNegativeEpoch,
            "negative replacement epoch preserves metadata");

        DirectiveSnapshot beforeNegativeFrames = SnapshotDirective(
            issued, issuedOwner);
        AssertArgumentOutOfRange(
            "replacementFrames",
            delegate { issued.RebaseInitialEpoch(4L, -1); },
            "negative replacement frames");
        AssertDirectiveSnapshot(
            issued,
            beforeNegativeFrames,
            "negative replacement frames preserve metadata");

        issued.RebaseInitialEpoch(0L, 0);
        Check.Equal(0L, issued.Epoch, "rebase accepts zero epoch");
        Check.Equal(0, issued.SettleFrames, "rebase accepts zero frames");
        Check.Equal(301L, issued.Id, "rebase preserves ID");
        Check.Equal(2.5, issued.NowSeconds, "rebase preserves time");
        Check.True(issued.Active, "rebased directive remains active");
        Check.True(
            issued.BelongsTo(issuedOwner),
            "rebase preserves owner identity");
        Check.False(issued.InspectGate, "rebase clears inspect flag");
        Check.False(
            issued.TimeoutAfterSample,
            "rebase clears timeout flag");

        issued.RebaseInitialEpoch(8L, 2);
        Check.Equal(8L, issued.Epoch, "repeated rebase replaces epoch");
        Check.Equal(
            2,
            issued.SettleFrames,
            "repeated rebase replaces frames");
        Check.Equal(301L, issued.Id, "repeated rebase preserves ID");
        Check.Equal(2.5, issued.NowSeconds, "repeated rebase preserves time");
        Check.True(issued.Active, "repeated rebase remains active");
        Check.True(
            issued.BelongsTo(issuedOwner),
            "repeated rebase preserves owner");
        Check.False(
            issued.InspectGate,
            "repeated rebase keeps inspect clear");
        Check.False(
            issued.TimeoutAfterSample,
            "repeated rebase keeps timeout clear");

        issued.RebaseInitialEpoch(Int64.MaxValue, Int32.MaxValue);
        Check.Equal(
            Int64.MaxValue,
            issued.Epoch,
            "rebase accepts maximum epoch");
        Check.Equal(
            Int32.MaxValue,
            issued.SettleFrames,
            "rebase accepts maximum frames");
        Check.Equal(301L, issued.Id, "maximum rebase preserves ID");
        Check.Equal(2.5, issued.NowSeconds, "maximum rebase preserves time");
        Check.True(issued.Active, "maximum rebase remains active");
        Check.True(
            issued.BelongsTo(issuedOwner),
            "maximum rebase preserves owner");
        Check.False(
            issued.InspectGate,
            "maximum rebase keeps inspect clear");
        Check.False(
            issued.TimeoutAfterSample,
            "maximum rebase keeps timeout clear");

        Check.True(
            issued.TryComplete(),
            "repeatedly rebased directive completes");
        DirectiveSnapshot consumed = SnapshotDirective(issued, issuedOwner);
        Check.Throws<InvalidOperationException>(
            delegate { issued.RebaseInitialEpoch(9L, 3); },
            "rebased consumed directive rejects rebase");
        AssertDirectiveSnapshot(
            issued,
            consumed,
            "consumed rebase rejection preserves metadata");
    }

    private static void AssertDirectiveCompetitions()
    {
        object authorizeOwner = new object();
        UpdateDirective authorize = UpdateDirective.Issued(
            authorizeOwner,
            7000000002L,
            1L,
            1,
            1.0,
            false,
            false);
        DirectiveSnapshot authorizeBefore = SnapshotDirective(
            authorize, authorizeOwner);
        int authorizeWinners = RunTwoWorkers(
            delegate { return authorize.TryAuthorize(); },
            delegate { return authorize.TryAuthorize(); },
            "directive authorize race");
        Check.Equal(
            1,
            authorizeWinners,
            "directive authorize race exactly one winner");
        AssertDirectiveSnapshot(
            authorize,
            authorizeBefore,
            "directive authorize race preserves metadata");
        Check.True(
            authorize.TryFail(),
            "directive authorize race cleanup succeeds");

        object completeOwner = new object();
        UpdateDirective complete = UpdateDirective.Issued(
            completeOwner,
            7000000003L,
            2L,
            2,
            2.0,
            true,
            false);
        Check.True(
            complete.TryAuthorize(),
            "directive complete race authorization succeeds");
        DirectiveSnapshot completeBefore = SnapshotDirective(
            complete, completeOwner);
        int completeWinners = RunTwoWorkers(
            delegate { return complete.TryComplete(); },
            delegate { return complete.TryComplete(); },
            "directive complete race");
        Check.Equal(
            1,
            completeWinners,
            "directive complete race exactly one winner");
        AssertDirectiveSnapshot(
            complete,
            completeBefore,
            "directive complete race preserves metadata");
        Check.False(
            complete.TryFail(),
            "directive complete race leaves consumed state");

        object issuedFailOwner = new object();
        UpdateDirective issuedFail = UpdateDirective.Issued(
            issuedFailOwner,
            7000000004L,
            3L,
            3,
            3.0,
            false,
            true);
        DirectiveSnapshot issuedFailBefore = SnapshotDirective(
            issuedFail, issuedFailOwner);
        int issuedFailWinners = RunTwoWorkers(
            delegate { return issuedFail.TryFail(); },
            delegate { return issuedFail.TryFail(); },
            "directive issued fail race");
        Check.Equal(
            1,
            issuedFailWinners,
            "directive issued fail race exactly one winner");
        AssertDirectiveSnapshot(
            issuedFail,
            issuedFailBefore,
            "directive issued fail race preserves metadata");
        Check.False(
            issuedFail.TryAuthorize(),
            "directive issued fail race leaves consumed state");

        object authorizedFailOwner = new object();
        UpdateDirective authorizedFail = UpdateDirective.Issued(
            authorizedFailOwner,
            7000000005L,
            4L,
            4,
            4.0,
            true,
            true);
        Check.True(
            authorizedFail.TryAuthorize(),
            "directive authorized fail race authorization succeeds");
        DirectiveSnapshot authorizedFailBefore = SnapshotDirective(
            authorizedFail, authorizedFailOwner);
        int authorizedFailWinners = RunTwoWorkers(
            delegate { return authorizedFail.TryFail(); },
            delegate { return authorizedFail.TryFail(); },
            "directive authorized fail race");
        Check.Equal(
            1,
            authorizedFailWinners,
            "directive authorized fail race exactly one winner");
        AssertDirectiveSnapshot(
            authorizedFail,
            authorizedFailBefore,
            "directive authorized fail race preserves metadata");
        Check.False(
            authorizedFail.TryComplete(),
            "directive authorized fail race leaves consumed state");

        object competingOwner = new object();
        UpdateDirective competing = UpdateDirective.Issued(
            competingOwner,
            7000000006L,
            5L,
            5,
            5.0,
            false,
            false);
        Check.True(
            competing.TryAuthorize(),
            "complete-fail race authorization succeeds");
        DirectiveSnapshot competingBefore = SnapshotDirective(
            competing, competingOwner);
        int competingWinners = RunTwoWorkers(
            delegate { return competing.TryComplete(); },
            delegate { return competing.TryFail(); },
            "directive complete-fail race");
        Check.Equal(
            1,
            competingWinners,
            "authorized completion and failure exactly one winner");
        AssertDirectiveSnapshot(
            competing,
            competingBefore,
            "complete-fail race preserves metadata");
        Check.False(
            competing.TryComplete(),
            "complete-fail race rejects later completion");
        Check.False(
            competing.TryFail(),
            "complete-fail race rejects later failure");
    }

    private static void AssertGateSampleContract()
    {
        AssertGlobalInternalEnum(typeof(GateSampleKind), "GateSampleKind");
        string[] names = new string[]
        {
            "NotInspected", "NonQuiescent", "Captured"
        };
        Check.Sequence(
            names,
            Enum.GetNames(typeof(GateSampleKind)),
            "gate sample kind names");
        int[] actualValues = new int[names.Length];
        for (int index = 0; index < names.Length; index++)
        {
            actualValues[index] = (int)Enum.Parse(
                typeof(GateSampleKind), names[index], false);
        }
        Check.Sequence(
            new int[] { 0, 1, 2 },
            actualValues,
            "gate sample kind numeric values");

        Type type = typeof(GateSample);
        AssertGlobalInternalSealed(type, "GateSample");
        ConstructorInfo[] constructors = type.GetConstructors(
            BindingFlags.Instance
            | BindingFlags.Public
            | BindingFlags.NonPublic
            | BindingFlags.DeclaredOnly);
        Check.Equal(1, constructors.Length, "GateSample constructor count");
        Check.True(
            constructors[0].IsPrivate,
            "GateSample constructor is private");
        ParameterInfo[] constructorParameters =
            constructors[0].GetParameters();
        Check.Equal(
            2,
            constructorParameters.Length,
            "GateSample constructor parameter count");
        Check.Equal(
            typeof(GateSampleKind),
            constructorParameters[0].ParameterType,
            "GateSample constructor kind type");
        Check.Equal(
            typeof(CaptureRecord),
            constructorParameters[1].ParameterType,
            "GateSample constructor capture type");

        GateSample notInspected = GateSample.NotInspected();
        Check.Equal(
            GateSampleKind.NotInspected,
            notInspected.Kind,
            "not-inspected sample kind");
        Check.True(
            notInspected.Capture == null,
            "not-inspected sample has null capture");

        GateSample nonQuiescent = GateSample.NonQuiescent();
        Check.Equal(
            GateSampleKind.NonQuiescent,
            nonQuiescent.Kind,
            "nonquiescent sample kind");
        Check.True(
            nonQuiescent.Capture == null,
            "nonquiescent sample has null capture");

        CaptureRecord capture = ProtocolSamples.Capture("gate-sample");
        GateSample captured = GateSample.Captured(capture);
        Check.Equal(
            GateSampleKind.Captured,
            captured.Kind,
            "captured sample kind");
        Check.Same(
            capture,
            captured.Capture,
            "captured sample preserves identity");
        AssertArgumentNull(
            "capture",
            delegate { GateSample.Captured(null); },
            "captured null rejected");
    }

    private static void AssertPassiveReporterContract()
    {
        Type type = typeof(IPassiveReporter);
        Check.True(type.Namespace == null, "IPassiveReporter global namespace");
        Check.True(type.IsNotPublic, "IPassiveReporter internal visibility");
        Check.True(type.IsInterface, "IPassiveReporter interface shape");

        MethodInfo[] methods = type.GetMethods(
            BindingFlags.Instance
            | BindingFlags.Public
            | BindingFlags.NonPublic
            | BindingFlags.DeclaredOnly);
        Check.Equal(4, methods.Length, "reporter method count");
        AssertReporterMethod(
            methods,
            "Ready",
            new Type[] { typeof(int) },
            new string[] { "completedInputs" });
        AssertReporterMethod(
            methods,
            "Complete",
            new Type[0],
            new string[0]);
        AssertReporterMethod(
            methods,
            "Failed",
            new Type[] { typeof(string) },
            new string[] { "code" });
        AssertReporterMethod(
            methods,
            "Diagnostic",
            new Type[] { typeof(string) },
            new string[] { "message" });

        BoundaryFakePassiveReporter fake = new BoundaryFakePassiveReporter();
        IPassiveReporter contract = fake;
        Check.Same(fake, contract, "fake reporter implements interface");
        fake.Ready(6);
        fake.Complete();
        fake.Failed("capture_failed");
        fake.Diagnostic("detail");
        Check.Equal(1, fake.ReadyCalls, "reporter Ready call count");
        Check.Equal(6, fake.CompletedInputs, "reporter Ready value");
        Check.Equal(1, fake.CompleteCalls, "reporter Complete call count");
        Check.Equal(1, fake.FailedCalls, "reporter Failed call count");
        Check.Equal(
            "capture_failed",
            fake.FailedCode,
            "reporter Failed value");
        Check.Equal(
            1,
            fake.DiagnosticCalls,
            "reporter Diagnostic call count");
        Check.Equal(
            "detail",
            fake.DiagnosticMessage,
            "reporter Diagnostic value");
    }

    private static void AssertReporterMethod(
        MethodInfo[] methods,
        string name,
        Type[] parameterTypes,
        string[] parameterNames)
    {
        MethodInfo found = null;
        for (int index = 0; index < methods.Length; index++)
        {
            if (String.Equals(
                    methods[index].Name,
                    name,
                    StringComparison.Ordinal))
            {
                Check.True(found == null, "reporter method unique " + name);
                found = methods[index];
            }
        }
        Check.True(found != null, "reporter method present " + name);
        Check.Equal(typeof(void), found.ReturnType, "reporter return " + name);
        Check.True(found.IsPublic, "reporter method public " + name);
        Check.True(found.IsAbstract, "reporter method abstract " + name);
        Check.False(found.IsStatic, "reporter method instance " + name);
        ParameterInfo[] parameters = found.GetParameters();
        Check.Equal(
            parameterTypes.Length,
            parameters.Length,
            "reporter parameter count " + name);
        Check.Equal(
            parameterTypes.Length,
            parameterNames.Length,
            "reporter expected parameter metadata " + name);
        for (int index = 0; index < parameters.Length; index++)
        {
            Check.Equal(
                parameterTypes[index],
                parameters[index].ParameterType,
                "reporter parameter type " + name + " " + index.ToString());
            Check.Equal(
                parameterNames[index],
                parameters[index].Name,
                "reporter parameter name " + name + " " + index.ToString());
        }
    }

    private static HookSnapshot SnapshotHook(
        HookToken token,
        object owner)
    {
        return new HookSnapshot
        {
            Owner = owner,
            Id = token.Id,
            Kind = token.Kind,
            Active = token.Active,
            BelongsToOwner = token.BelongsTo(owner)
        };
    }

    private static void AssertHookSnapshot(
        HookToken token,
        HookSnapshot expected,
        string label)
    {
        Check.Equal(expected.Id, token.Id, label + " ID");
        Check.Equal(expected.Kind, token.Kind, label + " kind");
        Check.Equal(expected.Active, token.Active, label + " active");
        Check.Equal(
            expected.BelongsToOwner,
            token.BelongsTo(expected.Owner),
            label + " owner identity");
        Check.False(
            token.BelongsTo(new object()),
            label + " rejects foreign owner");
    }

    private static DirectiveSnapshot SnapshotDirective(
        UpdateDirective directive,
        object owner)
    {
        return new DirectiveSnapshot
        {
            Owner = owner,
            Id = directive.Id,
            Epoch = directive.Epoch,
            SettleFrames = directive.SettleFrames,
            NowSeconds = directive.NowSeconds,
            Active = directive.Active,
            InspectGate = directive.InspectGate,
            TimeoutAfterSample = directive.TimeoutAfterSample,
            BelongsToOwner = directive.BelongsTo(owner)
        };
    }

    private static void AssertDirectiveSnapshot(
        UpdateDirective directive,
        DirectiveSnapshot expected,
        string label)
    {
        Check.Equal(expected.Id, directive.Id, label + " ID");
        Check.Equal(expected.Epoch, directive.Epoch, label + " epoch");
        Check.Equal(
            expected.SettleFrames,
            directive.SettleFrames,
            label + " settle frames");
        Check.Equal(
            expected.NowSeconds,
            directive.NowSeconds,
            label + " time");
        Check.Equal(expected.Active, directive.Active, label + " active");
        Check.Equal(
            expected.InspectGate,
            directive.InspectGate,
            label + " inspect flag");
        Check.Equal(
            expected.TimeoutAfterSample,
            directive.TimeoutAfterSample,
            label + " timeout flag");
        Check.Equal(
            expected.BelongsToOwner,
            directive.BelongsTo(expected.Owner),
            label + " owner identity");
        Check.False(
            directive.BelongsTo(new object()),
            label + " rejects foreign owner");
    }

    private static int RunTwoWorkers(
        Func<bool> leftAction,
        Func<bool> rightAction,
        string label)
    {
        if (leftAction == null)
            throw new ArgumentNullException("leftAction");
        if (rightAction == null)
            throw new ArgumentNullException("rightAction");

        ManualResetEvent startGate = new ManualResetEvent(false);
        ManualResetEvent leftReady = new ManualResetEvent(false);
        ManualResetEvent rightReady = new ManualResetEvent(false);
        bool[] results = new bool[2];
        Exception[] failures = new Exception[2];
        Thread left = CreateWorker(
            leftAction,
            startGate,
            leftReady,
            results,
            failures,
            0,
            label + " left");
        Thread right = CreateWorker(
            rightAction,
            startGate,
            rightReady,
            results,
            failures,
            1,
            label + " right");

        bool leftWasReady = false;
        bool rightWasReady = false;
        try
        {
            left.Start();
            right.Start();
            leftWasReady = leftReady.WaitOne(WorkerTimeoutMilliseconds);
            rightWasReady = rightReady.WaitOne(WorkerTimeoutMilliseconds);
        }
        finally
        {
            startGate.Set();
        }

        bool leftJoined = left.Join(WorkerTimeoutMilliseconds);
        bool rightJoined = right.Join(WorkerTimeoutMilliseconds);
        Check.True(leftWasReady, label + " left ready timeout");
        Check.True(rightWasReady, label + " right ready timeout");
        Check.True(leftJoined, label + " left join timeout");
        Check.True(rightJoined, label + " right join timeout");
        if (failures[0] != null)
        {
            throw new InvalidOperationException(
                label + " left worker failed", failures[0]);
        }
        if (failures[1] != null)
        {
            throw new InvalidOperationException(
                label + " right worker failed", failures[1]);
        }
        return (results[0] ? 1 : 0) + (results[1] ? 1 : 0);
    }

    private static Thread CreateWorker(
        Func<bool> action,
        ManualResetEvent startGate,
        ManualResetEvent ready,
        bool[] results,
        Exception[] failures,
        int index,
        string label)
    {
        Thread worker = new Thread(
            delegate()
            {
                try
                {
                    ready.Set();
                    if (!startGate.WaitOne(WorkerTimeoutMilliseconds))
                    {
                        throw new InvalidOperationException(
                            label + " start gate timeout");
                    }
                    results[index] = action();
                }
                catch (Exception error)
                {
                    failures[index] = error;
                }
            });
        worker.IsBackground = true;
        return worker;
    }

    private static void AssertGlobalInternalSealed(Type type, string label)
    {
        Check.True(type.Namespace == null, label + " global namespace");
        Check.True(type.IsNotPublic, label + " internal visibility");
        Check.True(type.IsClass, label + " class shape");
        Check.True(type.IsSealed, label + " sealed shape");
    }

    private static void AssertGlobalInternalEnum(Type type, string label)
    {
        Check.True(type.Namespace == null, label + " global namespace");
        Check.True(type.IsNotPublic, label + " internal visibility");
        Check.True(type.IsEnum, label + " enum shape");
        Check.Equal(
            typeof(int),
            Enum.GetUnderlyingType(type),
            label + " Int32 underlying type");
    }

    private static void AssertArgumentNull(
        string parameterName,
        Action action,
        string message)
    {
        ArgumentNullException error = Check.Throws<ArgumentNullException>(
            action, message);
        Check.Equal(parameterName, error.ParamName, message + " parameter");
    }

    private static void AssertArgumentOutOfRange(
        string parameterName,
        Action action,
        string message)
    {
        ArgumentOutOfRangeException error =
            Check.Throws<ArgumentOutOfRangeException>(action, message);
        Check.Equal(parameterName, error.ParamName, message + " parameter");
    }
}
