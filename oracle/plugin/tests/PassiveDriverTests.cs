internal static class PassiveDriverTests
{
    internal static void Register(TestRegistry tests)
    {
        PassiveDriverBoundaryTests.Register(tests);
        PassiveDriverInitialTests.Register(tests);
        PassiveDriverInputTests.Register(tests);
        PassiveDriverTerminalTests.Register(tests);
    }
}
