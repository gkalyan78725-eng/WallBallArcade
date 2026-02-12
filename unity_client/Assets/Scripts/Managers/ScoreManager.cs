using UnityEngine;
using UnityEngine.Events;

/// <summary>
/// Manages score, combo system, and high scores.
/// </summary>
public class ScoreManager : MonoBehaviour
{
    #region Configuration
    
    [Header("Combo Settings")]
    [SerializeField] private float comboTimeout = 2f;
    [SerializeField] private float maxComboMultiplier = 5f;
    [SerializeField] private int hitsPerComboLevel = 3;
    
    [Header("High Score")]
    [SerializeField] private string highScoreKey = "HighScore";
    
    #endregion
    
    #region State
    
    private int currentScore = 0;
    private int comboCount = 0;
    private float comboMultiplier = 1f;
    private float lastHitTime = 0f;
    private int highScore = 0;
    
    #endregion
    
    #region Events
    
    [Header("Events")]
    public UnityEvent<int> OnScoreChanged = new UnityEvent<int>();
    public UnityEvent<int, float> OnComboChanged = new UnityEvent<int, float>();
    public UnityEvent<int> OnNewHighScore = new UnityEvent<int>();
    
    #endregion
    
    #region Unity Lifecycle
    
    private void Start()
    {
        LoadHighScore();
        
        // Subscribe to event bus
        EventBus.Instance.Subscribe<HitEvent>(HandleHitEvent);
    }
    
    private void Update()
    {
        // Check combo timeout
        if (comboCount > 0 && Time.time - lastHitTime > comboTimeout)
        {
            ResetCombo();
        }
    }
    
    private void OnDestroy()
    {
        // Unsubscribe from event bus
        EventBus.Instance.Unsubscribe<HitEvent>(HandleHitEvent);
    }
    
    #endregion
    
    #region Score Management
    
    /// <summary>
    /// Add points to score with combo multiplier.
    /// </summary>
    /// <param name="points">Base points</param>
    public void AddScore(int points)
    {
        if (points <= 0)
            return;
        
        // Apply combo multiplier
        int finalPoints = Mathf.RoundToInt(points * comboMultiplier);
        currentScore += finalPoints;
        
        // Check high score
        if (currentScore > highScore)
        {
            highScore = currentScore;
            SaveHighScore();
            OnNewHighScore?.Invoke(highScore);
        }
        
        OnScoreChanged?.Invoke(currentScore);
        
        // Publish score event
        EventBus.Instance.Publish(new ScoreEvent(finalPoints, currentScore, Vector2.zero));
        
        Debug.Log($"Score added: {finalPoints} (base: {points}, multiplier: {comboMultiplier:F1}x), total: {currentScore}");
    }
    
    /// <summary>
    /// Reset score to zero.
    /// </summary>
    public void ResetScore()
    {
        currentScore = 0;
        ResetCombo();
        OnScoreChanged?.Invoke(currentScore);
        
        Debug.Log("Score reset");
    }
    
    /// <summary>
    /// Get current score.
    /// </summary>
    public int GetScore()
    {
        return currentScore;
    }
    
    #endregion
    
    #region Combo System
    
    /// <summary>
    /// Update combo counter.
    /// </summary>
    public void UpdateCombo()
    {
        comboCount++;
        lastHitTime = Time.time;
        
        // Calculate multiplier
        int comboLevel = comboCount / hitsPerComboLevel;
        comboMultiplier = Mathf.Min(1f + comboLevel * 0.5f, maxComboMultiplier);
        
        OnComboChanged?.Invoke(comboCount, comboMultiplier);
        
        // Publish combo event
        EventBus.Instance.Publish(new ComboEvent(comboCount, comboMultiplier));
        
        Debug.Log($"Combo: {comboCount} (multiplier: {comboMultiplier:F1}x)");
    }
    
    /// <summary>
    /// Reset combo counter.
    /// </summary>
    public void ResetCombo()
    {
        if (comboCount == 0)
            return;
        
        comboCount = 0;
        comboMultiplier = 1f;
        OnComboChanged?.Invoke(comboCount, comboMultiplier);
        
        Debug.Log("Combo reset");
    }
    
    /// <summary>
    /// Get current combo count.
    /// </summary>
    public int GetComboCount()
    {
        return comboCount;
    }
    
    /// <summary>
    /// Get current combo multiplier.
    /// </summary>
    public float GetComboMultiplier()
    {
        return comboMultiplier;
    }
    
    #endregion
    
    #region High Score
    
    private void LoadHighScore()
    {
        highScore = PlayerPrefs.GetInt(highScoreKey, 0);
        Debug.Log($"High score loaded: {highScore}");
    }
    
    private void SaveHighScore()
    {
        PlayerPrefs.SetInt(highScoreKey, highScore);
        PlayerPrefs.Save();
        Debug.Log($"High score saved: {highScore}");
    }
    
    /// <summary>
    /// Get high score.
    /// </summary>
    public int GetHighScore()
    {
        return highScore;
    }
    
    #endregion
    
    #region Event Handlers
    
    private void HandleHitEvent(HitEvent hitEvent)
    {
        UpdateCombo();
    }
    
    #endregion
}
