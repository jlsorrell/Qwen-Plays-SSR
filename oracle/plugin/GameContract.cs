using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

internal static class GameContract
{
    internal static void ValidateLegacySurface()
    {
        RequireMethod(typeof(Game), "Playerinputstring",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(Direction), new Type[0]);
        RequireMethod(typeof(Game), "DoPlayerInput",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(void), new Type[0]);
        RequireMethod(typeof(GameState), "ProcessInput",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(bool), new Type[] { typeof(Direction) });
    }

    internal static void ValidatePassiveSurface()
    {
        ValidateLegacySurface();
        RequireDirectionValue("North", 0);
        RequireDirectionValue("South", 1);
        RequireDirectionValue("West", 2);
        RequireDirectionValue("East", 3);
        RequireDirectionValue("None", 8);
        RequireMethod(typeof(Game), "Update",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(void), new Type[0]);
        RequireMethod(typeof(Game), "DoUndo",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(void), new Type[0]);
        RequireMethod(typeof(Game), "RestorePrevState",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(void), new Type[] { typeof(GameState.BakStruct) });
        RequireMethod(typeof(Game), "DoRestart",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(void), new Type[0]);
        RequireMethod(typeof(Game), "SetGameState",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(void), new Type[] { typeof(GameState) });
        RequireMethod(typeof(GameState), "Moving",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(bool), new Type[0]);
        RequireMethod(typeof(GameState), "Save",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(string), new Type[] { typeof(bool), typeof(bool) });

        RequireField(typeof(Game), "gamestate",
            BindingFlags.Instance | BindingFlags.Public, typeof(GameState));
        RequireField(typeof(Game), "exitSequence",
            BindingFlags.Instance | BindingFlags.Public, typeof(bool));
        RequireField(typeof(Game), "bluespawnanim",
            BindingFlags.Instance | BindingFlags.Public, typeof(bool));
        RequireField(typeof(Game), "escmenu",
            BindingFlags.Instance | BindingFlags.Public, typeof(GameObject));
        RequireField(typeof(Game), "endingsequence",
            BindingFlags.Static | BindingFlags.Public, typeof(bool));
        RequireField(typeof(Game), "leaving",
            BindingFlags.Instance | BindingFlags.NonPublic, typeof(bool));
        RequireField(typeof(Game), "gameover",
            BindingFlags.Instance | BindingFlags.NonPublic, typeof(bool));
        RequireField(typeof(Game), "exploding",
            BindingFlags.Instance | BindingFlags.NonPublic, typeof(bool));
        RequireField(typeof(GameState), "player",
            BindingFlags.Instance | BindingFlags.Public, typeof(Entity));
        RequireField(typeof(GameState), "movements",
            BindingFlags.Instance | BindingFlags.Public, typeof(List<Movement>));
        RequireField(typeof(GameState), "worldsausagespawns",
            BindingFlags.Instance | BindingFlags.Public, typeof(List<Coord>));
        RequireField(typeof(GameState), "pushestotry",
            BindingFlags.Instance | BindingFlags.Public, typeof(int));
        RequireField(typeof(GameState), "pushtargetlevel",
            BindingFlags.Instance | BindingFlags.Public, typeof(string));
        RequireField(typeof(GameState), "overworld",
            BindingFlags.Instance | BindingFlags.Public, typeof(bool));
        RequireField(typeof(GameState), "won",
            BindingFlags.Instance | BindingFlags.Public, typeof(bool));
        RequireField(typeof(GameState), "returning",
            BindingFlags.Instance | BindingFlags.Public, typeof(bool));
        RequireField(typeof(GameState), "haveevercookedall",
            BindingFlags.Instance | BindingFlags.Public, typeof(bool));
        RequireField(typeof(GameState), "lostreason",
            BindingFlags.Instance | BindingFlags.Public, typeof(string));
        RequireField(typeof(GameState), "displayname",
            BindingFlags.Instance | BindingFlags.Public, typeof(string));
        RequireField(typeof(GameState), "sausagescooked",
            BindingFlags.Instance | BindingFlags.Public, typeof(int));
        RequireField(typeof(GameState), "shouldredrawcoffins",
            BindingFlags.Static | BindingFlags.Public, typeof(Coord));
        RequireField(typeof(SaveGame), "homePath",
            BindingFlags.Static | BindingFlags.Public, typeof(string));
        RequireField(typeof(SaveGame), "PersistentDataPath",
            BindingFlags.Static | BindingFlags.Public, typeof(string));
    }

    private static MethodInfo RequireMethod(
        Type owner, string name, BindingFlags flags,
        Type returnType, Type[] parameters)
    {
        MethodInfo method = owner.GetMethod(name, flags, null, parameters, null);
        if (method == null || method.ReturnType != returnType
            || method.IsStatic != ((flags & BindingFlags.Static) != 0))
            throw new MissingMethodException(owner.FullName, name);
        return method;
    }

    private static FieldInfo RequireField(
        Type owner, string name, BindingFlags flags, Type fieldType)
    {
        FieldInfo field = owner.GetField(name, flags);
        if (field == null || field.FieldType != fieldType
            || field.IsStatic != ((flags & BindingFlags.Static) != 0))
            throw new MissingFieldException(owner.FullName, name);
        return field;
    }

    private static void RequireDirectionValue(string name, int expected)
    {
        FieldInfo field = typeof(Direction).GetField(
            name, BindingFlags.Public | BindingFlags.Static);
        if (field == null || !field.IsLiteral || field.FieldType != typeof(Direction))
            throw new MissingFieldException(typeof(Direction).FullName, name);
        object value = field.GetRawConstantValue();
        if (value == null || value.GetType() != typeof(int) || (int)value != expected)
            throw new InvalidOperationException("unexpected Direction value: " + name);
    }
}
