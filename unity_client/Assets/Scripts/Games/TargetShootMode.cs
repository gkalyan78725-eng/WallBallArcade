using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Target shoot game mode with random target spawning.
/// </summary>
public class TargetShootMode : MonoBehaviour, IGameMode
{
    #region Configuration
    
    [Header("Target Settings")]
    [SerializeField] private GameObject targetPrefab;
    [SerializeField] private int maxActiveTargets = 5;
    [SerializeField] private float minTargetSize = 0.5f;
    [SerializeField] private float maxTargetSize = 1.5f;
    
    [Header("Spawn Settings")]
    [SerializeField] private float spawnInterval = 2f;
    [SerializeField] private Vector2 spawnAreaMin = new Vector2(-4f, -4f);
    [SerializeField] private Vector2 spawnAreaMax = new Vector2(4f, 4f);
    
    [Header("Scoring")]
    [SerializeField] private int basePoints = 50;
    [SerializeField] private int sizeMultiplier = 100;
    
    [Header("Game Duration")]
    [SerializeField] private float gameDuration = 60f;
    
    [Header("Hit Detection")]
    [SerializeField] private float hitTolerance = 0.2f;
    
    #endregion
    
    #region State
    
    private List<Target> activeTargets = new List<Target>();
    private float nextSpawnTime = 0f;
    private float gameStartTime = 0f;
    private bool isGameOver = false;
    private int targetHits = 0;
    private int targetMisses = 0;
    
    #endregion
    
    #region IGameMode Implementation
    
    public void Initialize()
    {
        Reset();
        gameStartTime = Time.time;
        SpawnTarget();
        
        Debug.Log($"TargetShootMode initialized: {gameDuration}s duration");
    }
    
    public void OnHit(Vector2 worldPosition, float velocity)
    {
        // Find hit target
        Target hitTarget = FindTargetAtPosition(worldPosition);
        
        if (hitTarget != null)
        {
            DestroyTarget(hitTarget, true);
            targetHits++;
        }
        else
        {
            targetMisses++;
            Debug.Log($"Miss! Accuracy: {GetAccuracy():F1}%");
        }
    }
    
    public void Update()
    {
        // Check time limit
        float timeRemaining = gameDuration - (Time.time - gameStartTime);
        
        if (timeRemaining <= 0 && !isGameOver)
        {
            isGameOver = true;
            Debug.Log($"Time's up! Hits: {targetHits}, Accuracy: {GetAccuracy():F1}%");
            EventBus.Instance.Publish<GameOverEvent>();
        }
        
        // Update timer display
        if (UIManager.Instance != null)
        {
            UIManager.Instance.UpdateTimer(Mathf.Max(0, timeRemaining));
        }
        
        // Spawn new targets
        if (!isGameOver && Time.time >= nextSpawnTime && activeTargets.Count < maxActiveTargets)
        {
            SpawnTarget();
            nextSpawnTime = Time.time + spawnInterval;
        }
        
        // Remove expired targets
        for (int i = activeTargets.Count - 1; i >= 0; i--)
        {
            if (activeTargets[i].IsExpired())
            {
                DestroyTarget(activeTargets[i], false);
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
        ClearTargets();
        targetHits = 0;
        targetMisses = 0;
        isGameOver = false;
        nextSpawnTime = 0f;
    }
    
    #endregion
    
    #region Target Management
    
    private void SpawnTarget()
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
        
        // Random size (smaller = more points)
        float size = Random.Range(minTargetSize, maxTargetSize);
        
        // Spawn
        GameObject targetObj = Instantiate(targetPrefab, position, Quaternion.identity, transform);
        targetObj.transform.localScale = Vector3.one * size;
        
        Target target = new Target
        {
            GameObject = targetObj,
            Size = size,
            SpawnTime = Time.time,
            Lifetime = 10f
        };
        
        activeTargets.Add(target);
    }
    
    private Target FindTargetAtPosition(Vector2 worldPosition)
    {
        foreach (Target target in activeTargets)
        {
            if (target.GameObject == null)
                continue;
            
            float radius = target.Size / 2f + hitTolerance;
            float distance = Vector2.Distance(worldPosition, target.GameObject.transform.position);
            
            if (distance <= radius)
            {
                return target;
            }
        }
        
        return null;
    }
    
    private void DestroyTarget(Target target, bool wasHit)
    {
        if (target == null || target.GameObject == null)
            return;
        
        if (wasHit)
        {
            // Calculate points (smaller targets = more points)
            float sizeRatio = 1f - ((target.Size - minTargetSize) / (maxTargetSize - minTargetSize));
            int points = basePoints + Mathf.RoundToInt(sizeRatio * sizeMultiplier);
            
            // Add score
            ScoreManager scoreManager = FindObjectOfType<ScoreManager>();
            if (scoreManager != null)
            {
                scoreManager.AddScore(points);
            }
            
            // Play sound
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.PlaySFX("TargetHit", 0.8f, 1f + sizeRatio * 0.5f);
            }
            
            Debug.Log($"Target hit! Points: {points}");
        }
        
        // Remove and destroy
        activeTargets.Remove(target);
        Destroy(target.GameObject);
    }
    
    private void ClearTargets()
    {
        foreach (Target target in activeTargets)
        {
            if (target.GameObject != null)
            {
                Destroy(target.GameObject);
            }
        }
        
        activeTargets.Clear();
    }
    
    #endregion
    
    #region Statistics
    
    private float GetAccuracy()
    {
        int totalAttempts = targetHits + targetMisses;
        return totalAttempts > 0 ? (targetHits / (float)totalAttempts) * 100f : 0f;
    }
    
    #endregion
    
    #region Target Class
    
    private class Target
    {
        public GameObject GameObject;
        public float Size;
        public float SpawnTime;
        public float Lifetime;
        
        public bool IsExpired()
        {
            return Time.time - SpawnTime > Lifetime;
        }
    }
    
    #endregion
}
