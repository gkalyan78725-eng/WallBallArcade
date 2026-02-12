using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Reaction mode with quick hit timing challenges.
/// </summary>
public class ReactionMode : MonoBehaviour, IGameMode
{
    #region Configuration
    
    [Header("Target Settings")]
    [SerializeField] private GameObject targetPrefab;
    [SerializeField] private Vector2 spawnAreaMin = new Vector2(-4f, -4f);
    [SerializeField] private Vector2 spawnAreaMax = new Vector2(4f, 4f);
    
    [Header("Timing")]
    [SerializeField] private float minDisplayTime = 0.5f;
    [SerializeField] private float maxDisplayTime = 2f;
    [SerializeField] private float timeBetweenTargets = 0.3f;
    
    [Header("Scoring")]
    [SerializeField] private int fastHitBonus = 200;
    [SerializeField] private int mediumHitPoints = 100;
    [SerializeField] private int slowHitPoints = 50;
    [SerializeField] private float fastHitThreshold = 0.3f;
    [SerializeField] private float mediumHitThreshold = 0.7f;
    
    [Header("Difficulty")]
    [SerializeField] private int livesCount = 3;
    [SerializeField] private int targetCount = 20;
    
    [Header("Hit Detection")]
    [SerializeField] private float hitRadius = 0.5f;
    
    #endregion
    
    #region State
    
    private GameObject currentTarget;
    private float targetSpawnTime = 0f;
    private float targetExpireTime = 0f;
    private float nextTargetTime = 0f;
    
    private int remainingLives;
    private int targetsSpawned = 0;
    private bool isGameOver = false;
    
    private List<float> reactionTimes = new List<float>();
    
    #endregion
    
    #region IGameMode Implementation
    
    public void Initialize()
    {
        Reset();
        remainingLives = livesCount;
        SpawnNextTarget();
        
        Debug.Log($"ReactionMode initialized: {targetCount} targets, {livesCount} lives");
    }
    
    public void OnHit(Vector2 worldPosition, float velocity)
    {
        if (currentTarget == null)
        {
            // Miss - hit when no target
            return;
        }
        
        // Check if hit is within target radius
        float distance = Vector2.Distance(worldPosition, currentTarget.transform.position);
        
        if (distance <= hitRadius)
        {
            // Calculate reaction time
            float reactionTime = Time.time - targetSpawnTime;
            reactionTimes.Add(reactionTime);
            
            // Calculate points based on reaction time
            int points = CalculatePoints(reactionTime);
            
            // Add score
            ScoreManager scoreManager = FindObjectOfType<ScoreManager>();
            if (scoreManager != null)
            {
                scoreManager.AddScore(points);
            }
            
            // Play sound with pitch based on speed
            if (AudioManager.Instance != null)
            {
                float pitch = 1f + (1f - Mathf.Clamp01(reactionTime / maxDisplayTime)) * 0.5f;
                AudioManager.Instance.PlaySFX("QuickHit", 0.8f, pitch);
            }
            
            Debug.Log($"Hit! Reaction: {reactionTime:F3}s, Points: {points}");
            
            // Destroy target and prepare next
            DestroyCurrentTarget();
            nextTargetTime = Time.time + timeBetweenTargets;
        }
    }
    
    public void Update()
    {
        // Check if current target expired
        if (currentTarget != null && Time.time >= targetExpireTime)
        {
            // Miss - target expired
            remainingLives--;
            Debug.Log($"Miss! Lives remaining: {remainingLives}");
            
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.PlaySFX("Miss", 0.5f);
            }
            
            DestroyCurrentTarget();
            
            if (remainingLives <= 0)
            {
                isGameOver = true;
                Debug.Log($"Game Over! Average reaction: {GetAverageReactionTime():F3}s");
                EventBus.Instance.Publish<GameOverEvent>();
                return;
            }
            
            nextTargetTime = Time.time + timeBetweenTargets;
        }
        
        // Spawn next target
        if (currentTarget == null && Time.time >= nextTargetTime)
        {
            if (targetsSpawned < targetCount)
            {
                SpawnNextTarget();
            }
            else if (!isGameOver)
            {
                // All targets completed
                isGameOver = true;
                Debug.Log($"All targets completed! Average reaction: {GetAverageReactionTime():F3}s");
                EventBus.Instance.Publish<LevelCompleteEvent>();
            }
        }
    }
    
    public int GetScore()
    {
        ScoreManager scoreManager = FindObjectOfType<ScoreManager>();
        return scoreManager != null ? scoreManager.GetScore() : 0;
    }
    
    public bool IsGameOver()
    {
        return isGameOver;
    }
    
    public void Reset()
    {
        DestroyCurrentTarget();
        targetsSpawned = 0;
        remainingLives = livesCount;
        isGameOver = false;
        reactionTimes.Clear();
        nextTargetTime = 0f;
    }
    
    #endregion
    
    #region Target Management
    
    private void SpawnNextTarget()
    {
        if (targetPrefab == null)
        {
            Debug.LogError("Target prefab not assigned");
            return;
        }
        
        // Random position
        float x = Random.Range(spawnAreaMin.x, spawnAreaMax.x);
        float y = Random.Range(spawnAreaMin.y, spawnAreaMax.y);
        Vector3 position = new Vector3(x, y, 0);
        
        // Spawn
        currentTarget = Instantiate(targetPrefab, position, Quaternion.identity, transform);
        
        // Shorter display time as difficulty increases
        float difficultyFactor = targetsSpawned / (float)targetCount;
        float displayTime = Mathf.Lerp(maxDisplayTime, minDisplayTime, difficultyFactor);
        
        targetSpawnTime = Time.time;
        targetExpireTime = targetSpawnTime + displayTime;
        
        targetsSpawned++;
        
        Debug.Log($"Target {targetsSpawned}/{targetCount} spawned (display: {displayTime:F2}s)");
    }
    
    private void DestroyCurrentTarget()
    {
        if (currentTarget != null)
        {
            Destroy(currentTarget);
            currentTarget = null;
        }
    }
    
    #endregion
    
    #region Scoring
    
    private int CalculatePoints(float reactionTime)
    {
        if (reactionTime < fastHitThreshold)
        {
            return fastHitBonus;
        }
        else if (reactionTime < mediumHitThreshold)
        {
            return mediumHitPoints;
        }
        else
        {
            return slowHitPoints;
        }
    }
    
    #endregion
    
    #region Statistics
    
    private float GetAverageReactionTime()
    {
        if (reactionTimes.Count == 0)
            return 0f;
        
        float sum = 0f;
        foreach (float time in reactionTimes)
        {
            sum += time;
        }
        
        return sum / reactionTimes.Count;
    }
    
    #endregion
}
