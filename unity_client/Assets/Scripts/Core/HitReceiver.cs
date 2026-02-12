using UnityEngine;
using UnityEngine.Events;
using System;
using System.Collections.Generic;

/// <summary>
/// Receives hit events from vision engine and broadcasts to game systems.
/// </summary>
public class HitReceiver : MonoBehaviour
{
    #region Configuration
    
    [Header("Protocol")]
    [SerializeField] private NetworkProtocol protocol = NetworkProtocol.UDP;
    
    [Header("UDP Settings")]
    [SerializeField] private int udpPort = 9000;
    
    [Header("WebSocket Settings")]
    [SerializeField] private string websocketUri = "ws://localhost:9001";
    
    [Header("Coordinate Transform")]
    [SerializeField] private bool normalizeCoordinates = true;
    [SerializeField] private Vector2 worldSize = new Vector2(10f, 10f);
    [SerializeField] private Vector2 worldOffset = new Vector2(-5f, -5f);
    
    #endregion
    
    #region Network Protocol
    
    public enum NetworkProtocol
    {
        UDP,
        WebSocket
    }
    
    #endregion
    
    #region Events
    
    /// <summary>
    /// Event fired when hit is detected.
    /// Parameters: worldPosition, velocity
    /// </summary>
    [Header("Events")]
    public UnityEvent<Vector2, float> OnHitDetected = new UnityEvent<Vector2, float>();
    
    #endregion
    
    #region Network Components
    
    private UDPReceiver udpReceiver;
    private WebSocketReceiver websocketReceiver;
    
    #endregion
    
    #region Message Queue
    
    private readonly Queue<HitMessage> messageQueue = new Queue<HitMessage>();
    private readonly object queueLock = new object();
    
    #endregion
    
    #region Statistics
    
    private int messagesReceived = 0;
    private float lastHitTime = 0f;
    
    #endregion
    
    #region Unity Lifecycle
    
    private void Start()
    {
        InitializeNetworking();
    }
    
    private void Update()
    {
        ProcessMessages();
    }
    
    private void OnDestroy()
    {
        StopNetworking();
    }
    
    #endregion
    
    #region Networking
    
    private void InitializeNetworking()
    {
        Debug.Log($"Initializing HitReceiver with protocol: {protocol}");
        
        switch (protocol)
        {
            case NetworkProtocol.UDP:
                InitializeUDP();
                break;
                
            case NetworkProtocol.WebSocket:
                InitializeWebSocket();
                break;
        }
    }
    
    private void InitializeUDP()
    {
        // Create UDP receiver component
        udpReceiver = gameObject.AddComponent<UDPReceiver>();
        udpReceiver.Port = udpPort;
        udpReceiver.OnMessageReceived.AddListener(HandleNetworkMessage);
        
        Debug.Log($"UDP receiver initialized on port {udpPort}");
    }
    
    private void InitializeWebSocket()
    {
        // Create WebSocket receiver component
        websocketReceiver = gameObject.AddComponent<WebSocketReceiver>();
        websocketReceiver.Uri = websocketUri;
        websocketReceiver.OnMessageReceived.AddListener(HandleNetworkMessage);
        
        Debug.Log($"WebSocket receiver initialized: {websocketUri}");
    }
    
    private void StopNetworking()
    {
        if (udpReceiver != null)
        {
            udpReceiver.OnMessageReceived.RemoveListener(HandleNetworkMessage);
            Destroy(udpReceiver);
        }
        
        if (websocketReceiver != null)
        {
            websocketReceiver.OnMessageReceived.RemoveListener(HandleNetworkMessage);
            Destroy(websocketReceiver);
        }
        
        Debug.Log("HitReceiver stopped");
    }
    
    #endregion
    
    #region Message Handling
    
    private void HandleNetworkMessage(string json)
    {
        try
        {
            // Parse JSON
            HitMessage message = JsonUtility.FromJson<HitMessage>(json);
            
            if (message == null || message.type != "hit")
            {
                return;
            }
            
            // Add to thread-safe queue
            lock (queueLock)
            {
                messageQueue.Enqueue(message);
            }
        }
        catch (Exception e)
        {
            Debug.LogWarning($"Failed to parse hit message: {e.Message}");
        }
    }
    
    private void ProcessMessages()
    {
        // Process all queued messages
        lock (queueLock)
        {
            while (messageQueue.Count > 0)
            {
                HitMessage message = messageQueue.Dequeue();
                ProcessHit(message);
            }
        }
    }
    
    private void ProcessHit(HitMessage message)
    {
        // Transform coordinates
        Vector2 worldPosition = TransformCoordinates(message.x, message.y);
        
        // Update statistics
        messagesReceived++;
        lastHitTime = Time.time;
        
        // Broadcast event
        OnHitDetected?.Invoke(worldPosition, message.velocity);
        
        Debug.Log($"Hit received: pos=({worldPosition.x:F2}, {worldPosition.y:F2}), vel={message.velocity:F1}");
    }
    
    #endregion
    
    #region Coordinate Transform
    
    private Vector2 TransformCoordinates(float x, float y)
    {
        if (normalizeCoordinates)
        {
            // Assume x, y are in range [0, wall_width] and [0, wall_height]
            // Normalize and map to world space
            float normalizedX = x / 1920f; // Assuming 1920 wall width
            float normalizedY = y / 1080f; // Assuming 1080 wall height
            
            float worldX = worldOffset.x + normalizedX * worldSize.x;
            float worldY = worldOffset.y + normalizedY * worldSize.y;
            
            return new Vector2(worldX, worldY);
        }
        else
        {
            // Use coordinates directly
            return new Vector2(x, y);
        }
    }
    
    #endregion
    
    #region Public Methods
    
    /// <summary>
    /// Get number of messages received.
    /// </summary>
    public int GetMessageCount()
    {
        return messagesReceived;
    }
    
    /// <summary>
    /// Get time since last hit.
    /// </summary>
    public float GetTimeSinceLastHit()
    {
        return Time.time - lastHitTime;
    }
    
    /// <summary>
    /// Check if receiver is connected.
    /// </summary>
    public bool IsConnected()
    {
        if (protocol == NetworkProtocol.UDP && udpReceiver != null)
        {
            return udpReceiver.IsListening();
        }
        
        if (protocol == NetworkProtocol.WebSocket && websocketReceiver != null)
        {
            return websocketReceiver.IsConnected();
        }
        
        return false;
    }
    
    #endregion
    
    #region Message Class
    
    [Serializable]
    private class HitMessage
    {
        public string type;
        public float x;
        public float y;
        public float velocity;
        public float timestamp;
    }
    
    #endregion
}
