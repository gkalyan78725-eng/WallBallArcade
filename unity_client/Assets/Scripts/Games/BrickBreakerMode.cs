using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Brick breaker game mode with destructible bricks.
/// </summary>
public class BrickBreakerMode : MonoBehaviour, IGameMode
{
    #region Configuration
    
    [Header("Brick Settings")]
    [SerializeField] private GameObject brickPrefab;
    [SerializeField] private int rows = 5;
    [SerializeField] private int columns = 10;
    [SerializeField] private float brickWidth = 0.8f;
    [SerializeField] private float brickHeight = 0.3f;
    [SerializeField] private float spacing = 0.1f;
    
    [Header("Scoring")]
    [SerializeField] private int pointsPerBrick = 100;
    [SerializeField] private int bonusPointsTopRow = 50;
    
    [Header("Hit Detection")]
    [SerializeField] private float hitRadius = 0.5f;
    
    [Header("Effects")]
    [SerializeField] private GameObject explosionPrefab;
    
    #endregion
    
    #region State
    
    private List<GameObject> bricks = new List<GameObject>();
    private int bricksDestroyed = 0;
    private bool isGameOver = false;
    
    #endregion
    
    #region IGameMode Implementation
    
    public void Initialize()
    {
        Reset();
        SpawnBricks();
        
        Debug.Log($"BrickBreakerMode initialized: {rows}x{columns} grid");
    }
    
    public void OnHit(Vector2 worldPosition, float velocity)
    {
        // Find nearest brick
        GameObject hitBrick = FindBrickAtPosition(worldPosition);
        
        if (hitBrick != null)
        {
            DestroyBrick(hitBrick, worldPosition);
        }
    }
    
    public void Update()
    {
        // Check win condition
        if (bricks.Count == 0 && !isGameOver)
        {
            isGameOver = true;
            Debug.Log("Level complete!");
            EventBus.Instance.Publish<LevelCompleteEvent>();
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
        ClearBricks();
        bricksDestroyed = 0;
        isGameOver = false;
    }
    
    #endregion
    
    #region Brick Management
    
    private void SpawnBricks()
    {
        if (brickPrefab == null)
        {
            Debug.LogError("Brick prefab not assigned");
            return;
        }
        
        float totalWidth = columns * brickWidth + (columns - 1) * spacing;
        float totalHeight = rows * brickHeight + (rows - 1) * spacing;
        
        float startX = -totalWidth / 2f;
        float startY = totalHeight / 2f;
        
        for (int row = 0; row < rows; row++)
        {
            for (int col = 0; col < columns; col++)
            {
                float x = startX + col * (brickWidth + spacing) + brickWidth / 2f;
                float y = startY - row * (brickHeight + spacing) - brickHeight / 2f;
                
                Vector3 position = new Vector3(x, y, 0);
                GameObject brick = Instantiate(brickPrefab, position, Quaternion.identity, transform);
                
                // Color gradient based on row
                SpriteRenderer renderer = brick.GetComponent<SpriteRenderer>();
                if (renderer != null)
                {
                    float hue = row / (float)rows;
                    renderer.color = Color.HSVToRGB(hue, 0.8f, 1f);
                }
                
                bricks.Add(brick);
            }
        }
        
        Debug.Log($"Spawned {bricks.Count} bricks");
    }
    
    private GameObject FindBrickAtPosition(Vector2 worldPosition)
    {
        GameObject nearestBrick = null;
        float nearestDistance = float.MaxValue;
        
        foreach (GameObject brick in bricks)
        {
            if (brick == null)
                continue;
            
            float distance = Vector2.Distance(worldPosition, brick.transform.position);
            
            if (distance < hitRadius && distance < nearestDistance)
            {
                nearestDistance = distance;
                nearestBrick = brick;
            }
        }
        
        return nearestBrick;
    }
    
    private void DestroyBrick(GameObject brick, Vector2 hitPosition)
    {
        if (brick == null)
            return;
        
        // Calculate points
        int points = pointsPerBrick;
        
        // Bonus for top row
        if (brick.transform.position.y > 3f)
        {
            points += bonusPointsTopRow;
        }
        
        // Add score
        ScoreManager scoreManager = FindObjectOfType<ScoreManager>();
        if (scoreManager != null)
        {
            scoreManager.AddScore(points);
        }
        
        // Spawn explosion effect
        if (explosionPrefab != null)
        {
            Instantiate(explosionPrefab, brick.transform.position, Quaternion.identity);
        }
        
        // Play sound
        if (AudioManager.Instance != null)
        {
            AudioManager.Instance.PlaySFX("BrickBreak", 0.7f);
        }
        
        // Remove and destroy
        bricks.Remove(brick);
        Destroy(brick);
        
        bricksDestroyed++;
        
        Debug.Log($"Brick destroyed ({bricksDestroyed}/{rows * columns})");
    }
    
    private void ClearBricks()
    {
        foreach (GameObject brick in bricks)
        {
            if (brick != null)
            {
                Destroy(brick);
            }
        }
        
        bricks.Clear();
    }
    
    #endregion
}
