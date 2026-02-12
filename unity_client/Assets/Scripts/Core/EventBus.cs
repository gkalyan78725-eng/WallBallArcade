using System;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Generic event bus for decoupled communication between systems.
/// </summary>
public class EventBus
{
    #region Singleton
    
    private static EventBus instance;
    
    public static EventBus Instance
    {
        get
        {
            if (instance == null)
            {
                instance = new EventBus();
            }
            return instance;
        }
    }
    
    #endregion
    
    #region Event Storage
    
    private readonly Dictionary<Type, List<Delegate>> eventHandlers = new Dictionary<Type, List<Delegate>>();
    
    #endregion
    
    #region Subscribe
    
    /// <summary>
    /// Subscribe to an event type.
    /// </summary>
    /// <typeparam name="T">Event data type</typeparam>
    /// <param name="handler">Handler action</param>
    public void Subscribe<T>(Action<T> handler)
    {
        Type eventType = typeof(T);
        
        if (!eventHandlers.ContainsKey(eventType))
        {
            eventHandlers[eventType] = new List<Delegate>();
        }
        
        if (!eventHandlers[eventType].Contains(handler))
        {
            eventHandlers[eventType].Add(handler);
        }
    }
    
    /// <summary>
    /// Subscribe to an event type with no parameters.
    /// </summary>
    /// <typeparam name="T">Event type marker</typeparam>
    /// <param name="handler">Handler action</param>
    public void Subscribe<T>(Action handler)
    {
        Type eventType = typeof(T);
        
        if (!eventHandlers.ContainsKey(eventType))
        {
            eventHandlers[eventType] = new List<Delegate>();
        }
        
        if (!eventHandlers[eventType].Contains(handler))
        {
            eventHandlers[eventType].Add(handler);
        }
    }
    
    #endregion
    
    #region Unsubscribe
    
    /// <summary>
    /// Unsubscribe from an event type.
    /// </summary>
    /// <typeparam name="T">Event data type</typeparam>
    /// <param name="handler">Handler action</param>
    public void Unsubscribe<T>(Action<T> handler)
    {
        Type eventType = typeof(T);
        
        if (eventHandlers.ContainsKey(eventType))
        {
            eventHandlers[eventType].Remove(handler);
            
            // Clean up empty lists
            if (eventHandlers[eventType].Count == 0)
            {
                eventHandlers.Remove(eventType);
            }
        }
    }
    
    /// <summary>
    /// Unsubscribe from an event type with no parameters.
    /// </summary>
    /// <typeparam name="T">Event type marker</typeparam>
    /// <param name="handler">Handler action</param>
    public void Unsubscribe<T>(Action handler)
    {
        Type eventType = typeof(T);
        
        if (eventHandlers.ContainsKey(eventType))
        {
            eventHandlers[eventType].Remove(handler);
            
            // Clean up empty lists
            if (eventHandlers[eventType].Count == 0)
            {
                eventHandlers.Remove(eventType);
            }
        }
    }
    
    #endregion
    
    #region Publish
    
    /// <summary>
    /// Publish an event with data.
    /// </summary>
    /// <typeparam name="T">Event data type</typeparam>
    /// <param name="eventData">Event data</param>
    public void Publish<T>(T eventData)
    {
        Type eventType = typeof(T);
        
        if (!eventHandlers.ContainsKey(eventType))
        {
            return;
        }
        
        // Create a copy to avoid modification during iteration
        List<Delegate> handlers = new List<Delegate>(eventHandlers[eventType]);
        
        foreach (Delegate handler in handlers)
        {
            try
            {
                (handler as Action<T>)?.Invoke(eventData);
            }
            catch (Exception e)
            {
                Debug.LogError($"Error invoking event handler: {e.Message}");
            }
        }
    }
    
    /// <summary>
    /// Publish an event with no data.
    /// </summary>
    /// <typeparam name="T">Event type marker</typeparam>
    public void Publish<T>()
    {
        Type eventType = typeof(T);
        
        if (!eventHandlers.ContainsKey(eventType))
        {
            return;
        }
        
        // Create a copy to avoid modification during iteration
        List<Delegate> handlers = new List<Delegate>(eventHandlers[eventType]);
        
        foreach (Delegate handler in handlers)
        {
            try
            {
                (handler as Action)?.Invoke();
            }
            catch (Exception e)
            {
                Debug.LogError($"Error invoking event handler: {e.Message}");
            }
        }
    }
    
    #endregion
    
    #region Clear
    
    /// <summary>
    /// Clear all event handlers.
    /// </summary>
    public void ClearAll()
    {
        eventHandlers.Clear();
    }
    
    /// <summary>
    /// Clear handlers for a specific event type.
    /// </summary>
    /// <typeparam name="T">Event type</typeparam>
    public void Clear<T>()
    {
        Type eventType = typeof(T);
        
        if (eventHandlers.ContainsKey(eventType))
        {
            eventHandlers.Remove(eventType);
        }
    }
    
    #endregion
}

#region Event Types

/// <summary>
/// Hit event data.
/// </summary>
public struct HitEvent
{
    public Vector2 Position;
    public float Velocity;
    public float Timestamp;
    
    public HitEvent(Vector2 position, float velocity, float timestamp)
    {
        Position = position;
        Velocity = velocity;
        Timestamp = timestamp;
    }
}

/// <summary>
/// Score event data.
/// </summary>
public struct ScoreEvent
{
    public int Points;
    public int TotalScore;
    public Vector2 Position;
    
    public ScoreEvent(int points, int totalScore, Vector2 position)
    {
        Points = points;
        TotalScore = totalScore;
        Position = position;
    }
}

/// <summary>
/// Combo event data.
/// </summary>
public struct ComboEvent
{
    public int ComboCount;
    public float Multiplier;
    
    public ComboEvent(int comboCount, float multiplier)
    {
        ComboCount = comboCount;
        Multiplier = multiplier;
    }
}

/// <summary>
/// Game state event data.
/// </summary>
public struct GameStateEvent
{
    public GameManager.GameState State;
    
    public GameStateEvent(GameManager.GameState state)
    {
        State = state;
    }
}

/// <summary>
/// Game over event marker.
/// </summary>
public struct GameOverEvent
{
}

/// <summary>
/// Level complete event marker.
/// </summary>
public struct LevelCompleteEvent
{
}

#endregion
