using System;

internal static class GameObservationTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("observation", "all thirteen gates are required",
            EveryGateRequired);
        tests.Add("observation", "capture maps all twelve fields", MapsAllFields);
        tests.Add("observation", "three nullable strings normalize",
            NullableStringsNormalize);
        tests.Add("observation", "required values reject null",
            RequiredValuesRejectNull);
        tests.Add("observation", "numeric ranges reject negative",
            NegativeNumbersReject);
    }

    private static GameGateValues Gates(bool[] values)
    {
        return new GameGateValues(
            values[0], values[1], values[2], values[3], values[4],
            values[5], values[6], values[7], values[8], values[9],
            values[10], values[11], values[12]);
    }

    private static void EveryGateRequired()
    {
        bool[] all = new bool[13];
        for (int index = 0; index < all.Length; index++) all[index] = true;
        Check.True(GameObservationPolicy.IsQuiescent(Gates(all)), "all gates");
        for (int index = 0; index < all.Length; index++)
        {
            bool[] changed = (bool[])all.Clone();
            changed[index] = false;
            Check.False(GameObservationPolicy.IsQuiescent(Gates(changed)),
                "gate " + index.ToString());
        }
    }

    private static CaptureValues Values(
        string rawSave, string identity, string level, string lost,
        string display, int cooked, int movements, int pushes)
    {
        return new CaptureValues(rawSave, identity, level, true, false, true,
            false, lost, display, cooked, movements, pushes);
    }

    private static void MapsAllFields()
    {
        CaptureRecord value = CaptureMapping.Create(new CaptureValues(
            "raw", "-17", "level", true, false, true, false,
            "lost", "display", Int32.MaxValue, Int32.MaxValue, Int32.MaxValue));
        Check.Equal("raw", value.RawSave, "raw");
        Check.Equal("-17", value.StateIdentity, "identity");
        Check.Equal("level", value.Level, "level");
        Check.True(value.Overworld, "overworld");
        Check.False(value.Won, "won");
        Check.True(value.Returning, "returning");
        Check.False(value.HaveEverCookedAll, "cooked all");
        Check.Equal("lost", value.LostReason, "lost");
        Check.Equal("display", value.DisplayName, "display");
        Check.Equal(Int32.MaxValue, value.SausagesCooked, "cooked");
        Check.Equal(Int32.MaxValue, value.MovementCount, "movement");
        Check.Equal(Int32.MaxValue, value.PushesToTry, "pushes");
    }

    private static void NullableStringsNormalize()
    {
        CaptureRecord value = CaptureMapping.Create(Values(
            "raw", "0", null, null, null, 0, 0, 0));
        Check.Equal("", value.Level, "level");
        Check.Equal("", value.LostReason, "lost");
        Check.Equal("", value.DisplayName, "display");
    }

    private static void RequiredValuesRejectNull()
    {
        Check.Throws<CaptureException>(
            delegate { CaptureMapping.Create(null); }, "values");
        Check.Throws<CaptureException>(
            delegate { CaptureMapping.Create(Values(
                null, "0", "", "", "", 0, 0, 0)); }, "raw");
        Check.Throws<CaptureException>(
            delegate { CaptureMapping.Create(Values(
                "raw", null, "", "", "", 0, 0, 0)); }, "identity");
    }

    private static void NegativeNumbersReject()
    {
        int[,] values = new int[,] { { -1, 0, 0 }, { 0, -1, 0 }, { 0, 0, -1 } };
        for (int index = 0; index < values.GetLength(0); index++)
        {
            int row = index;
            Check.Throws<CaptureException>(delegate
            {
                CaptureMapping.Create(Values("raw", "0", "", "", "",
                    values[row, 0], values[row, 1], values[row, 2]));
            }, "negative " + index.ToString());
        }
    }
}
