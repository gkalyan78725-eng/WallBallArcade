using UnityEngine;
using UnityEngine.Events;

/// <summary>
/// Main game manager singleton controlling game state and flow.
/// </summary>
public class GameManager : MonoBehaviour
{
    #region Singleton
    
    public static GameManager Instance { get; private set; }
    
    #endregion
    
    #region Game State
    
    /// <summary>
    /// Game state enumeration.
    /// </summary>
    public enum GameState
    {
        Menu,
        Playing,
        Paused,
        GameOver
    }
    
    [Header("Game State")]
    [SerializeField] private GameState currentState = GameState.Menu;
    
    /// <summary>
    /// Current game state (read-only).
    /// </summary>
    public GameState CurrentState => currentState;
    
    #endregion
    
    #region Game Mode
    
    [Header("Game Mode")]
    [SerializeField] private MonoBehaviour currentGameModeComponent;
    
    private IGameMode currentGameMode;
    
    #endregion
    
    #region Events
    
    [Header("Events")]
    public UnityEvent<GameState> OnStateChanged = new UnityEvent<GameState>();
    public UnityEvent<int> OnScoreUpdated = new UnityEvent<int>();
    public UnityEvent OnGameStarted = new UnityEvent();
    public UnityEvent OnGameEnded = new UnityEvent();
    
    #endregion
    
    #region Unity Lifecycle
    
    private void Awake()
    {
        // Singleton pattern
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        
        Instance = this;
        DontDestroyOnLoad(gameObject);
        
        Debug.Log("GameManager initialized");
    }
    
    private void Start()
    {
        // Subscribe to hit events
        HitReceiver hitReceiver = FindObjectOfType<HitReceiver>();
        if (hitReceiver != null)
        {
            hitReceiver.OnHitDetected.AddListener(HandleHit);
        }
        else
        {
            Debug.LogWarning("HitReceiver not found in scene");
        }
    }
    
    private void Update()
    {
        // Update current game mode
        if (currentState == GameState.Playing && currentGameMode != null)
        {
            currentGameMode.Update();
            
            // Check game over condition
            if (currentGameMode.IsGameOver())
            {
                EndGame();
            }
        }
        
        // Handle pause input
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            if (currentState == GameState.Playing)
            {
                PauseGame();
            }
            else if (currentState == GameState.Paused)
            {
                ResumeGame();
            }
        }
    }
    
    private void OnDestroy()
    {
        // Unsubscribe from events
        HitReceiver hitReceiver = FindObjectOfType<HitReceiver>();
        if (hitReceiver != null)
        {
            hitReceiver.OnHitDetected.RemoveListener(HandleHit);
        }
    }
    
    #endregion
    
    #region Game Control
    
    /// <summary>
    /// Start a new game with the specified game mode.
    /// </summary>
    /// <param name="gameModeComponent">Game mode component implementing IGameMode</param>
    public void StartGame(MonoBehaviour gameModeComponent)
    {
        if (gameModeComponent == null)
        {
            Debug.LogError("Game mode component is null");
            return;
        }
        
        IGameMode gameMode = gameModeComponent as IGameMode;
        if (gameMode == null)
        {
            Debug.LogError("Component does not implement IGameMode interface");
            return;
        }
        
        currentGameModeComponent = gameModeComponent;
        currentGameMode = gameMode;
        
        // Initialize game mode
        currentGameMode.Initialize();
        
        // Change state
        ChangeState(GameState.Playing);
        
        // Reset score
        ScoreManager scoreManager = FindObjectOfType<ScoreManager>();
        if (scoreManager != null)
        {
            scoreManager.ResetScore();
        }
        
        OnGameStarted?.Invoke();
        
        Debug.Log($"Game started with mode: {gameModeComponent.GetType().Name}");
    }
    
    /// <summary>
    /// Pause the current game.
    /// </summary>
    public void PauseGame()
    {
        if (currentState != GameState.Playing)
            return;
        
        ChangeState(GameState.Paused);
        Time.timeScale = 0f;
        
        Debug.Log("Game paused");
    }
    
    /// <summary>
    /// Resume the paused game.
    /// </summary>
    public void ResumeGame()
    {
        if (currentState != GameState.Paused)
            return;
        
        ChangeState(GameState.Playing);
        Time.timeScale = 1f;
        
        Debug.Log("Game resumed");
    }
    
    /// <summary>
    /// End the current game.
    /// </summary>
    public void EndGame()
    {
        if (currentState != GameState.Playing && currentState != GameState.Paused)
            return;
        
        ChangeState(GameState.GameOver);
        Time.timeScale = 1f;
        
        // Get final score
        if (currentGameMode != null)
        {
            int finalScore = currentGameMode.GetScore();
            OnScoreUpdated?.Invoke(finalScore);
            
            Debug.Log($"Game over. Final score: {finalScore}");
        }
        
        OnGameEnded?.Invoke();
    }
    
    /// <summary>
    /// Return to menu.
    /// </summary>
    public void ReturnToMenu()
    {
        ChangeState(GameState.Menu);
        Time.timeScale = 1f;
        
        // Reset game mode
        if (currentGameMode != null)
        {
            currentGameMode.Reset();
            currentGameMode = null;
            currentGameModeComponent = null;
        }
        
        Debug.Log("Returned to menu");
    }
    
    /// <summary>
    /// Restart the current game.
    /// </summary>
    public void RestartGame()
    {
        if (currentGameModeComponent == null)
        {
            Debug.LogWarning("No game mode to restart");
            return;
        }
        
        StartGame(currentGameModeComponent);
    }
    
    #endregion
    
    #region State Management
    
    private void ChangeState(GameState newState)
    {
        if (currentState == newState)
            return;
        
        GameState oldState = currentState;
        currentState = newState;
        
        OnStateChanged?.Invoke(newState);
        
        Debug.Log($"State changed: {oldState} -> {newState}");
    }
    
    #endregion
    
    #region Hit Handling
    
    private void HandleHit(Vector2 worldPosition, float velocity)
    {
        if (currentState != GameState.Playing || currentGameMode == null)
            return;
        
        // Forward hit to current game mode
        currentGameMode.OnHit(worldPosition, velocity);
    }
    
    #endregion
    
    #region Public Properties
    
    /// <summary>
    /// Get current game mode.
    /// </summary>
    public IGameMode CurrentGameMode => currentGameMode;
    
    /// <summary>
    /// Check if game is playing.
    /// </summary>
    public bool IsPlaying => currentState == GameState.Playing;
    
    /// <summary>
    /// Check if game is paused.
    /// </summary>
    public bool IsPaused => currentState == GameState.Paused;
    
    #endregion
}
