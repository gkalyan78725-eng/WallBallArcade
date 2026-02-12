using UnityEngine;
using TMPro;

/// <summary>
/// Manages calibration display and validation.
/// </summary>
public class CalibrationManager : MonoBehaviour
{
    #region Configuration
    
    [Header("Calibration Display")]
    [SerializeField] private bool showCalibrationGrid = false;
    [SerializeField] private int gridLines = 10;
    [SerializeField] private Color gridColor = Color.yellow;
    
    [Header("Test Mode")]
    [SerializeField] private bool testMode = false;
    [SerializeField] private GameObject hitMarkerPrefab;
    
    [Header("UI")]
    [SerializeField] private TextMeshProUGUI coordinateText;
    [SerializeField] private GameObject calibrationPanel;
    
    #endregion
    
    #region State
    
    private HitReceiver hitReceiver;
    
    #endregion
    
    #region Unity Lifecycle
    
    private void Start()
    {
        hitReceiver = FindObjectOfType<HitReceiver>();
        
        if (testMode && hitReceiver != null)
        {
            hitReceiver.OnHitDetected.AddListener(OnTestHit);
        }
        
        UpdateCalibrationDisplay();
    }
    
    private void Update()
    {
        // Toggle calibration display
        if (Input.GetKeyDown(KeyCode.C))
        {
            showCalibrationGrid = !showCalibrationGrid;
            UpdateCalibrationDisplay();
        }
        
        // Update coordinate display
        if (testMode && coordinateText != null && hitReceiver != null)
        {
            coordinateText.text = $"Messages: {hitReceiver.GetMessageCount()}\n" +
                                 $"Connected: {hitReceiver.IsConnected()}\n" +
                                 $"Last Hit: {hitReceiver.GetTimeSinceLastHit():F1}s ago";
        }
    }
    
    private void OnDestroy()
    {
        if (testMode && hitReceiver != null)
        {
            hitReceiver.OnHitDetected.RemoveListener(OnTestHit);
        }
    }
    
    #endregion
    
    #region Calibration Display
    
    private void UpdateCalibrationDisplay()
    {
        if (calibrationPanel != null)
        {
            calibrationPanel.SetActive(showCalibrationGrid);
        }
    }
    
    private void OnDrawGizmos()
    {
        if (!showCalibrationGrid)
            return;
        
        Gizmos.color = gridColor;
        
        // Draw grid in world space
        float worldWidth = 10f;
        float worldHeight = 10f;
        float worldOffsetX = -5f;
        float worldOffsetY = -5f;
        
        // Horizontal lines
        for (int i = 0; i <= gridLines; i++)
        {
            float y = worldOffsetY + (i / (float)gridLines) * worldHeight;
            Vector3 start = new Vector3(worldOffsetX, y, 0);
            Vector3 end = new Vector3(worldOffsetX + worldWidth, y, 0);
            Gizmos.DrawLine(start, end);
        }
        
        // Vertical lines
        for (int i = 0; i <= gridLines; i++)
        {
            float x = worldOffsetX + (i / (float)gridLines) * worldWidth;
            Vector3 start = new Vector3(x, worldOffsetY, 0);
            Vector3 end = new Vector3(x, worldOffsetY + worldHeight, 0);
            Gizmos.DrawLine(start, end);
        }
    }
    
    #endregion
    
    #region Test Mode
    
    private void OnTestHit(Vector2 worldPosition, float velocity)
    {
        if (!testMode || hitMarkerPrefab == null)
            return;
        
        // Spawn hit marker at position
        Vector3 position3D = new Vector3(worldPosition.x, worldPosition.y, 0);
        GameObject marker = Instantiate(hitMarkerPrefab, position3D, Quaternion.identity);
        
        // Auto-destroy after 2 seconds
        Destroy(marker, 2f);
        
        Debug.Log($"Test hit at {worldPosition} with velocity {velocity}");
    }
    
    #endregion
}
