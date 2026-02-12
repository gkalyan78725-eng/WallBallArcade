using UnityEngine;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// Manages UI panels, score display, and menu navigation.
/// </summary>
public class UIManager : MonoBehaviour
{
    #region Singleton
    
    public static UIManager Instance { get; private set; }
    
    #endregion
    
    #region UI Panels
    
    [Header("Panels")]
    [SerializeField] private GameObject menuPanel;
    [SerializeField] private GameObject gamePanel;
    [SerializeField] private GameObject pausePanel;
    [SerializeField] private GameObject gameOverPanel;
    
    #endregion
    
    #region UI Elements
    
    [Header("Game UI")]
    [SerializeField] private TextMeshProUGUI scoreText;
    [SerializeField] private TextMeshProUGUI comboText;
    [SerializeField] private TextMeshProUGUI timerText;
    
    [Header("Game Over UI")]
    [SerializeField] private TextMeshProUGUI finalScoreText;
    [SerializeField] private TextMeshProUGUI highScoreText;
    
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
        
        Debug.Log("UIManager initialized");
    }
    
    private void Start()
    {
        ShowMenu();
        
        // Subscribe to game events
        if (GameManager.Instance != null)
        {
            GameManager.Instance.OnStateChanged.AddListener(HandleStateChange);
        }
        
        // Subscribe to score events
        ScoreManager scoreManager = FindObjectOfType<ScoreManager>();
        if (scoreManager != null)
        {
            scoreManager.OnScoreChanged.AddListener(UpdateScore);
            scoreManager.OnComboChanged.AddListener(UpdateCombo);
        }
    }
    
    private void OnDestroy()
    {
        // Unsubscribe from events
        if (GameManager.Instance != null)
        {
            GameManager.Instance.OnStateChanged.RemoveListener(HandleStateChange);
        }
    }
    
    #endregion
    
    #region Panel Management
    
    /// <summary>
    /// Show menu panel.
    /// </summary>
    public void ShowMenu()
    {
        SetPanelActive(menuPanel, true);
        SetPanelActive(gamePanel, false);
        SetPanelActive(pausePanel, false);
        SetPanelActive(gameOverPanel, false);
    }
    
    /// <summary>
    /// Show game panel.
    /// </summary>
    public void ShowGame()
    {
        SetPanelActive(menuPanel, false);
        SetPanelActive(gamePanel, true);
        SetPanelActive(pausePanel, false);
        SetPanelActive(gameOverPanel, false);
        
        // Reset displays
        UpdateScore(0);
        UpdateCombo(0, 1f);
    }
    
    /// <summary>
    /// Show pause panel.
    /// </summary>
    public void ShowPause()
    {
        SetPanelActive(pausePanel, true);
    }
    
    /// <summary>
    /// Hide pause panel.
    /// </summary>
    public void HidePause()
    {
        SetPanelActive(pausePanel, false);
    }
    
    /// <summary>
    /// Show game over panel.
    /// </summary>
    public void ShowGameOver(int finalScore, int highScore)
    {
        SetPanelActive(gamePanel, false);
        SetPanelActive(gameOverPanel, true);
        
        if (finalScoreText != null)
        {
            finalScoreText.text = $"Score: {finalScore}";
        }
        
        if (highScoreText != null)
        {
            highScoreText.text = $"High Score: {highScore}";
        }
    }
    
    private void SetPanelActive(GameObject panel, bool active)
    {
        if (panel != null)
        {
            panel.SetActive(active);
        }
    }
    
    #endregion
    
    #region Display Updates
    
    /// <summary>
    /// Update score display.
    /// </summary>
    /// <param name="score">Current score</param>
    public void UpdateScore(int score)
    {
        if (scoreText != null)
        {
            scoreText.text = $"Score: {score}";
        }
    }
    
    /// <summary>
    /// Update combo display.
    /// </summary>
    /// <param name="comboCount">Combo count</param>
    /// <param name="multiplier">Combo multiplier</param>
    public void UpdateCombo(int comboCount, float multiplier)
    {
        if (comboText != null)
        {
            if (comboCount > 0)
            {
                comboText.text = $"Combo: {comboCount}x ({multiplier:F1}x)";
                comboText.gameObject.SetActive(true);
            }
            else
            {
                comboText.gameObject.SetActive(false);
            }
        }
    }
    
    /// <summary>
    /// Update timer display.
    /// </summary>
    /// <param name="timeRemaining">Time remaining in seconds</param>
    public void UpdateTimer(float timeRemaining)
    {
        if (timerText != null)
        {
            int minutes = Mathf.FloorToInt(timeRemaining / 60f);
            int seconds = Mathf.FloorToInt(timeRemaining % 60f);
            timerText.text = $"{minutes:00}:{seconds:00}";
        }
    }
    
    #endregion
    
    #region Event Handlers
    
    private void HandleStateChange(GameManager.GameState newState)
    {
        switch (newState)
        {
            case GameManager.GameState.Menu:
                ShowMenu();
                break;
                
            case GameManager.GameState.Playing:
                ShowGame();
                break;
                
            case GameManager.GameState.Paused:
                ShowPause();
                break;
                
            case GameManager.GameState.GameOver:
                ScoreManager scoreManager = FindObjectOfType<ScoreManager>();
                if (scoreManager != null)
                {
                    ShowGameOver(scoreManager.GetScore(), scoreManager.GetHighScore());
                }
                break;
        }
    }
    
    #endregion
    
    #region Button Handlers
    
    /// <summary>
    /// Handle resume button click.
    /// </summary>
    public void OnResumeClicked()
    {
        if (GameManager.Instance != null)
        {
            GameManager.Instance.ResumeGame();
        }
    }
    
    /// <summary>
    /// Handle restart button click.
    /// </summary>
    public void OnRestartClicked()
    {
        if (GameManager.Instance != null)
        {
            GameManager.Instance.RestartGame();
        }
    }
    
    /// <summary>
    /// Handle menu button click.
    /// </summary>
    public void OnMenuClicked()
    {
        if (GameManager.Instance != null)
        {
            GameManager.Instance.ReturnToMenu();
        }
    }
    
    #endregion
}
