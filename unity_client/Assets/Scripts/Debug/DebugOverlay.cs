using UnityEngine;
using TMPro;
using System.Text;

/// <summary>
/// Debug overlay for development and troubleshooting.
/// </summary>
public class DebugOverlay : MonoBehaviour
{
    #region Configuration
    
    [Header("Display Settings")]
    [SerializeField] private bool showOnStart = true;
    [SerializeField] private KeyCode toggleKey = KeyCode.F1;
    
    [Header("UI")]
    [SerializeField] private GameObject overlayPanel;
    [SerializeField] private TextMeshProUGUI debugText;
    
    [Header("Visualization")]
    [SerializeField] private GameObject hitMarkerPrefab;
    [SerializeField] private float hitMarkerLifetime = 1f;
    
    #endregion
    
    #region State
    
    private bool isVisible;
    private HitReceiver hitReceiver;
    private ScoreManager scoreManager;
    private float lastUpdateTime;
    private int frameCount;
    private float fps;
    
    #endregion
    
    #region Unity Lifecycle
    
    private void Start()
    {
        hitReceiver = FindObjectOfType<HitReceiver>();
        scoreManager = FindObjectOfType<ScoreManager>();
        
        isVisible = showOnStart;
        UpdateVisibility();
        
        // Subscribe to hit events
        if (hitReceiver != null)
        {
            hitReceiver.OnHitDetected.AddListener(OnDebugHit);
        }
    }
    
    private void Update()
    {
        // Toggle visibility
        if (Input.GetKeyDown(toggleKey))
        {
            isVisible = !isVisible;
            UpdateVisibility();
        }
        
        if (isVisible)
        {
            UpdateDebugInfo();
        }
        
        // Calculate FPS
        frameCount++;
        if (Time.time - lastUpdateTime >= 1f)
        {
            fps = frameCount / (Time.time - lastUpdateTime);
            frameCount = 0;
            lastUpdateTime = Time.time;
        }
    }
    
    private void OnDestroy()
    {
        if (hitReceiver != null)
        {
            hitReceiver.OnHitDetected.RemoveListener(OnDebugHit);
        }
    }
    
    #endregion
    
    #region Visibility
    
    private void UpdateVisibility()
    {
        if (overlayPanel != null)
        {
            overlayPanel.SetActive(isVisible);
        }
    }
    
    #endregion
    
    #region Debug Info
    
    private void UpdateDebugInfo()
    {
        if (debugText == null)
            return;
        
        StringBuilder sb = new StringBuilder();
        
        // Performance
        sb.AppendLine("=== PERFORMANCE ===");
        sb.AppendLine($"FPS: {fps:F1}");
        sb.AppendLine($"Frame Time: {Time.deltaTime * 1000:F2}ms");
        sb.AppendLine();
        
        // Network
        sb.AppendLine("=== NETWORK ===");
        if (hitReceiver != null)
        {
            sb.AppendLine($"Connected: {hitReceiver.IsConnected()}");
            sb.AppendLine($"Messages: {hitReceiver.GetMessageCount()}");
            sb.AppendLine($"Last Hit: {hitReceiver.GetTimeSinceLastHit():F1}s ago");
        }
        else
        {
            sb.AppendLine("HitReceiver: NOT FOUND");
        }
        sb.AppendLine();
        
        // Game State
        sb.AppendLine("=== GAME STATE ===");
        if (GameManager.Instance != null)
        {
            sb.AppendLine($"State: {GameManager.Instance.CurrentState}");
            sb.AppendLine($"Mode: {GameManager.Instance.CurrentGameMode?.GetType().Name ?? "None"}");
        }
        else
        {
            sb.AppendLine("GameManager: NOT FOUND");
        }
        sb.AppendLine();
        
        // Score
        sb.AppendLine("=== SCORE ===");
        if (scoreManager != null)
        {
            sb.AppendLine($"Score: {scoreManager.GetScore()}");
            sb.AppendLine($"Combo: {scoreManager.GetComboCount()}x ({scoreManager.GetComboMultiplier():F1}x)");
            sb.AppendLine($"High Score: {scoreManager.GetHighScore()}");
        }
        else
        {
            sb.AppendLine("ScoreManager: NOT FOUND");
        }
        sb.AppendLine();
        
        // Controls
        sb.AppendLine("=== CONTROLS ===");
        sb.AppendLine($"Toggle Debug: {toggleKey}");
        sb.AppendLine("Pause: ESC");
        
        debugText.text = sb.ToString();
    }
    
    #endregion
    
    #region Hit Visualization
    
    private void OnDebugHit(Vector2 worldPosition, float velocity)
    {
        if (!isVisible || hitMarkerPrefab == null)
            return;
        
        // Spawn hit marker
        Vector3 position3D = new Vector3(worldPosition.x, worldPosition.y, 0);
        GameObject marker = Instantiate(hitMarkerPrefab, position3D, Quaternion.identity);
        
        // Color based on velocity
        SpriteRenderer renderer = marker.GetComponent<SpriteRenderer>();
        if (renderer != null)
        {
            float normalizedVelocity = Mathf.Clamp01(velocity / 100f);
            renderer.color = Color.Lerp(Color.green, Color.red, normalizedVelocity);
        }
        
        // Auto-destroy
        Destroy(marker, hitMarkerLifetime);
    }
    
    #endregion
    
    #region Public Methods
    
    /// <summary>
    /// Show debug overlay.
    /// </summary>
    public void Show()
    {
        isVisible = true;
        UpdateVisibility();
    }
    
    /// <summary>
    /// Hide debug overlay.
    /// </summary>
    public void Hide()
    {
        isVisible = false;
        UpdateVisibility();
    }
    
    /// <summary>
    /// Toggle debug overlay.
    /// </summary>
    public void Toggle()
    {
        isVisible = !isVisible;
        UpdateVisibility();
    }
    
    #endregion
}
