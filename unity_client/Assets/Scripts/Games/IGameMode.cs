/// <summary>
/// Interface for game modes.
/// </summary>
public interface IGameMode
{
    /// <summary>
    /// Initialize the game mode.
    /// </summary>
    void Initialize();
    
    /// <summary>
    /// Handle hit event.
    /// </summary>
    /// <param name="worldPosition">Hit position in world space</param>
    /// <param name="velocity">Hit velocity</param>
    void OnHit(UnityEngine.Vector2 worldPosition, float velocity);
    
    /// <summary>
    /// Update game mode logic (called every frame).
    /// </summary>
    void Update();
    
    /// <summary>
    /// Get current score.
    /// </summary>
    /// <returns>Current score</returns>
    int GetScore();
    
    /// <summary>
    /// Check if game is over.
    /// </summary>
    /// <returns>True if game over</returns>
    bool IsGameOver();
    
    /// <summary>
    /// Reset game mode.
    /// </summary>
    void Reset();
}
