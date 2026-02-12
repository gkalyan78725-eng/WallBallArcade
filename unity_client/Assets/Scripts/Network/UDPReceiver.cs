using UnityEngine;
using UnityEngine.Events;
using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

/// <summary>
/// Async UDP receiver for network messages.
/// </summary>
public class UDPReceiver : MonoBehaviour
{
    #region Configuration
    
    public int Port = 9000;
    
    #endregion
    
    #region Events
    
    public UnityEvent<string> OnMessageReceived = new UnityEvent<string>();
    
    #endregion
    
    #region Network
    
    private UdpClient udpClient;
    private Thread receiveThread;
    private bool isRunning = false;
    
    #endregion
    
    #region Statistics
    
    private int messagesReceived = 0;
    
    #endregion
    
    #region Unity Lifecycle
    
    private void Start()
    {
        StartListening();
    }
    
    private void OnDestroy()
    {
        StopListening();
    }
    
    private void OnApplicationQuit()
    {
        StopListening();
    }
    
    #endregion
    
    #region Listening
    
    private void StartListening()
    {
        try
        {
            udpClient = new UdpClient(Port);
            isRunning = true;
            
            receiveThread = new Thread(ReceiveData);
            receiveThread.IsBackground = true;
            receiveThread.Start();
            
            Debug.Log($"UDP receiver started on port {Port}");
        }
        catch (Exception e)
        {
            Debug.LogError($"Failed to start UDP receiver: {e.Message}");
        }
    }
    
    private void StopListening()
    {
        isRunning = false;
        
        if (receiveThread != null && receiveThread.IsAlive)
        {
            receiveThread.Abort();
        }
        
        if (udpClient != null)
        {
            udpClient.Close();
            udpClient = null;
        }
        
        Debug.Log("UDP receiver stopped");
    }
    
    #endregion
    
    #region Receive Thread
    
    private void ReceiveData()
    {
        while (isRunning)
        {
            try
            {
                IPEndPoint remoteEndPoint = new IPEndPoint(IPAddress.Any, 0);
                byte[] data = udpClient.Receive(ref remoteEndPoint);
                
                string message = Encoding.UTF8.GetString(data);
                
                messagesReceived++;
                
                // Invoke event on main thread
                UnityMainThreadDispatcher.Instance.Enqueue(() =>
                {
                    OnMessageReceived?.Invoke(message);
                });
            }
            catch (ThreadAbortException)
            {
                break;
            }
            catch (Exception e)
            {
                Debug.LogWarning($"UDP receive error: {e.Message}");
            }
        }
    }
    
    #endregion
    
    #region Public Methods
    
    /// <summary>
    /// Check if receiver is listening.
    /// </summary>
    public bool IsListening()
    {
        return isRunning && udpClient != null;
    }
    
    /// <summary>
    /// Get number of messages received.
    /// </summary>
    public int GetMessageCount()
    {
        return messagesReceived;
    }
    
    #endregion
}

/// <summary>
/// Helper class to execute actions on the main Unity thread.
/// </summary>
public class UnityMainThreadDispatcher : MonoBehaviour
{
    private static UnityMainThreadDispatcher instance;
    private static readonly System.Collections.Generic.Queue<Action> executionQueue = new System.Collections.Generic.Queue<Action>();
    
    public static UnityMainThreadDispatcher Instance
    {
        get
        {
            if (instance == null)
            {
                GameObject obj = new GameObject("UnityMainThreadDispatcher");
                instance = obj.AddComponent<UnityMainThreadDispatcher>();
                DontDestroyOnLoad(obj);
            }
            return instance;
        }
    }
    
    private void Update()
    {
        lock (executionQueue)
        {
            while (executionQueue.Count > 0)
            {
                executionQueue.Dequeue()?.Invoke();
            }
        }
    }
    
    public void Enqueue(Action action)
    {
        lock (executionQueue)
        {
            executionQueue.Enqueue(action);
        }
    }
}
