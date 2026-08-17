using System;

internal static class PluginModePolicy
{
    internal static void StartOff(
        OracleConfiguration configuration,
        Action validateLegacySurface,
        Action emitBootMarker)
    {
        if (configuration == null) throw new ArgumentNullException("configuration");
        if (validateLegacySurface == null)
            throw new ArgumentNullException("validateLegacySurface");
        if (emitBootMarker == null) throw new ArgumentNullException("emitBootMarker");
        if (configuration.Mode != OracleMode.Off)
            throw new OracleConfigurationException("invalid_mode",
                new ArgumentException("Off policy requires off mode"));
        validateLegacySurface();
        emitBootMarker();
    }
}
