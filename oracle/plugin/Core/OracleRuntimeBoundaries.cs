using System;

internal interface IPassiveLog
{
    void Info(string message);
    void Error(string message);
    void Warning(string message);
}

internal interface IOracleGameAdapter
{
    void AuthenticateAndRedirectSavePath(string isolatedPath);
    bool VerifySavePath();
    bool TryGetState(object game, out object stateReference);
    bool IsQuiescent(object game, object verifiedState);
    bool MovementScheduled(object stateReference);
    bool CurrentMovementScheduled(object game);
    CaptureRecord Capture(object verifiedState);
    void InvokeUndo(object game);
}

internal interface IOracleRuntimeHost
{
    void ValidateAssemblyAndPassiveContract();
    ITraceSink CreateTrace(string outputDirectory, string runName);
    void InstallPatches(OracleController controller);
    void UnpatchSelf(OracleController controller);
    double NowSeconds();
    DateTime UtcNow();
}
