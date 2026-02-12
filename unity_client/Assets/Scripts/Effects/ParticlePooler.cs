using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Generic object pooler for particle systems and other reusable objects.
/// </summary>
public class ParticlePooler : MonoBehaviour
{
    #region Configuration
    
    [Header("Pool Settings")]
    public GameObject Prefab;
    public int PoolSize = 10;
    public bool AutoExpand = true;
    
    [Header("Return Settings")]
    [SerializeField] private float autoReturnTime = 2f;
    [SerializeField] private bool autoReturnOnParticleEnd = true;
    
    #endregion
    
    #region Pool
    
    private Queue<GameObject> pool = new Queue<GameObject>();
    private List<GameObject> activeObjects = new List<GameObject>();
    
    #endregion
    
    #region Statistics
    
    private int objectsCreated = 0;
    private int objectsReused = 0;
    
    #endregion
    
    #region Initialization
    
    /// <summary>
    /// Initialize the pool.
    /// </summary>
    public void Initialize()
    {
        if (Prefab == null)
        {
            Debug.LogError("Prefab not assigned to ParticlePooler");
            return;
        }
        
        // Pre-create pool objects
        for (int i = 0; i < PoolSize; i++)
        {
            CreateNewObject();
        }
        
        Debug.Log($"ParticlePooler initialized: {PoolSize} objects");
    }
    
    private GameObject CreateNewObject()
    {
        GameObject obj = Instantiate(Prefab, transform);
        obj.SetActive(false);
        pool.Enqueue(obj);
        objectsCreated++;
        
        return obj;
    }
    
    #endregion
    
    #region Get/Return
    
    /// <summary>
    /// Get an object from the pool.
    /// </summary>
    /// <returns>Pooled object</returns>
    public GameObject Get()
    {
        GameObject obj;
        
        if (pool.Count > 0)
        {
            obj = pool.Dequeue();
            objectsReused++;
        }
        else if (AutoExpand)
        {
            obj = CreateNewObject();
        }
        else
        {
            Debug.LogWarning("Pool exhausted and auto-expand disabled");
            return null;
        }
        
        obj.SetActive(true);
        activeObjects.Add(obj);
        
        // Start auto-return timer
        if (autoReturnTime > 0)
        {
            StartCoroutine(AutoReturnCoroutine(obj, autoReturnTime));
        }
        
        // Handle particle system auto-return
        if (autoReturnOnParticleEnd)
        {
            ParticleSystem ps = obj.GetComponent<ParticleSystem>();
            if (ps != null)
            {
                StartCoroutine(WaitForParticleEnd(obj, ps));
            }
        }
        
        return obj;
    }
    
    /// <summary>
    /// Return an object to the pool.
    /// </summary>
    /// <param name="obj">Object to return</param>
    public void Return(GameObject obj)
    {
        if (obj == null)
            return;
        
        obj.SetActive(false);
        activeObjects.Remove(obj);
        
        if (!pool.Contains(obj))
        {
            pool.Enqueue(obj);
        }
    }
    
    #endregion
    
    #region Auto-Return
    
    private System.Collections.IEnumerator AutoReturnCoroutine(GameObject obj, float delay)
    {
        yield return new WaitForSeconds(delay);
        
        if (obj != null && obj.activeSelf)
        {
            Return(obj);
        }
    }
    
    private System.Collections.IEnumerator WaitForParticleEnd(GameObject obj, ParticleSystem ps)
    {
        yield return new WaitForSeconds(0.1f);
        
        while (obj != null && ps != null && ps.isPlaying)
        {
            yield return new WaitForSeconds(0.1f);
        }
        
        if (obj != null && obj.activeSelf)
        {
            Return(obj);
        }
    }
    
    #endregion
    
    #region Statistics
    
    /// <summary>
    /// Get pool statistics.
    /// </summary>
    public string GetStatistics()
    {
        return $"Pool: {pool.Count} available, {activeObjects.Count} active, " +
               $"{objectsCreated} created, {objectsReused} reused";
    }
    
    #endregion
}
