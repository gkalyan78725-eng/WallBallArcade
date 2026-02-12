using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Manages hit effect spawning and lifecycle.
/// </summary>
public class HitEffectManager : MonoBehaviour
{
    #region Singleton
    
    public static HitEffectManager Instance { get; private set; }
    
    #endregion
    
    #region Configuration
    
    [Header("Effect Prefabs")]
    [SerializeField] private GameObject hitEffectPrefab;
    [SerializeField] private GameObject explosionEffectPrefab;
    [SerializeField] private GameObject sparkEffectPrefab;
    
    [Header("Settings")]
    [SerializeField] private float effectLifetime = 2f;
    [SerializeField] private bool usePooling = true;
    
    #endregion
    
    #region Pooling
    
    private ParticlePooler hitEffectPool;
    private ParticlePooler explosionEffectPool;
    private ParticlePooler sparkEffectPool;
    
    private List<GameObject> activeEffects = new List<GameObject>();
    
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
        
        InitializePools();
        
        Debug.Log("HitEffectManager initialized");
    }
    
    private void Update()
    {
        // Clean up expired effects
        for (int i = activeEffects.Count - 1; i >= 0; i--)
        {
            if (activeEffects[i] == null)
            {
                activeEffects.RemoveAt(i);
            }
        }
    }
    
    #endregion
    
    #region Initialization
    
    private void InitializePools()
    {
        if (!usePooling)
            return;
        
        // Create poolers
        if (hitEffectPrefab != null)
        {
            GameObject poolObj = new GameObject("HitEffectPool");
            poolObj.transform.SetParent(transform);
            hitEffectPool = poolObj.AddComponent<ParticlePooler>();
            hitEffectPool.Prefab = hitEffectPrefab;
            hitEffectPool.PoolSize = 10;
            hitEffectPool.Initialize();
        }
        
        if (explosionEffectPrefab != null)
        {
            GameObject poolObj = new GameObject("ExplosionEffectPool");
            poolObj.transform.SetParent(transform);
            explosionEffectPool = poolObj.AddComponent<ParticlePooler>();
            explosionEffectPool.Prefab = explosionEffectPrefab;
            explosionEffectPool.PoolSize = 5;
            explosionEffectPool.Initialize();
        }
        
        if (sparkEffectPrefab != null)
        {
            GameObject poolObj = new GameObject("SparkEffectPool");
            poolObj.transform.SetParent(transform);
            sparkEffectPool = poolObj.AddComponent<ParticlePooler>();
            sparkEffectPool.Prefab = sparkEffectPrefab;
            sparkEffectPool.PoolSize = 10;
            sparkEffectPool.Initialize();
        }
    }
    
    #endregion
    
    #region Effect Spawning
    
    /// <summary>
    /// Spawn hit effect at position.
    /// </summary>
    /// <param name="position">World position</param>
    /// <param name="color">Effect color</param>
    public void SpawnHitEffect(Vector3 position, Color? color = null)
    {
        GameObject effect = SpawnEffect(hitEffectPrefab, hitEffectPool, position);
        
        if (effect != null && color.HasValue)
        {
            ApplyColor(effect, color.Value);
        }
    }
    
    /// <summary>
    /// Spawn explosion effect at position.
    /// </summary>
    /// <param name="position">World position</param>
    /// <param name="scale">Effect scale</param>
    public void SpawnExplosionEffect(Vector3 position, float scale = 1f)
    {
        GameObject effect = SpawnEffect(explosionEffectPrefab, explosionEffectPool, position);
        
        if (effect != null)
        {
            effect.transform.localScale = Vector3.one * scale;
        }
    }
    
    /// <summary>
    /// Spawn spark effect at position.
    /// </summary>
    /// <param name="position">World position</param>
    public void SpawnSparkEffect(Vector3 position)
    {
        SpawnEffect(sparkEffectPrefab, sparkEffectPool, position);
    }
    
    private GameObject SpawnEffect(GameObject prefab, ParticlePooler pool, Vector3 position)
    {
        if (prefab == null)
            return null;
        
        GameObject effect;
        
        if (usePooling && pool != null)
        {
            effect = pool.Get();
            effect.transform.position = position;
        }
        else
        {
            effect = Instantiate(prefab, position, Quaternion.identity);
            Destroy(effect, effectLifetime);
        }
        
        activeEffects.Add(effect);
        
        return effect;
    }
    
    #endregion
    
    #region Color Management
    
    private void ApplyColor(GameObject effect, Color color)
    {
        ParticleSystem ps = effect.GetComponent<ParticleSystem>();
        if (ps != null)
        {
            var main = ps.main;
            main.startColor = color;
        }
        
        // Also check child particle systems
        ParticleSystem[] childSystems = effect.GetComponentsInChildren<ParticleSystem>();
        foreach (ParticleSystem childPs in childSystems)
        {
            var main = childPs.main;
            main.startColor = color;
        }
    }
    
    #endregion
}
