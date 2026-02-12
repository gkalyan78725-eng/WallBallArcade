using UnityEngine;
using System.Collections.Generic;
using System.Linq;

/// <summary>
/// Manages audio playback with pooling and priority system.
/// </summary>
[RequireComponent(typeof(AudioSource))]
public class AudioManager : MonoBehaviour
{
    #region Singleton
    
    public static AudioManager Instance { get; private set; }
    
    #endregion
    
    #region Configuration
    
    [Header("Audio Sources")]
    [SerializeField] private int audioSourcePoolSize = 10;
    
    [Header("Volume Categories")]
    [SerializeField, Range(0f, 1f)] private float masterVolume = 1f;
    [SerializeField, Range(0f, 1f)] private float sfxVolume = 1f;
    [SerializeField, Range(0f, 1f)] private float musicVolume = 1f;
    
    #endregion
    
    #region Audio Source Pool
    
    private List<AudioSource> audioSourcePool = new List<AudioSource>();
    private Dictionary<string, AudioClip> audioClipCache = new Dictionary<string, AudioClip>();
    
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
        DontDestroyOnLoad(gameObject);
        
        InitializeAudioPool();
        
        Debug.Log("AudioManager initialized");
    }
    
    #endregion
    
    #region Initialization
    
    private void InitializeAudioPool()
    {
        for (int i = 0; i < audioSourcePoolSize; i++)
        {
            GameObject audioObj = new GameObject($"AudioSource_{i}");
            audioObj.transform.SetParent(transform);
            
            AudioSource source = audioObj.AddComponent<AudioSource>();
            source.playOnAwake = false;
            
            audioSourcePool.Add(source);
        }
        
        Debug.Log($"Audio source pool created: {audioSourcePoolSize} sources");
    }
    
    #endregion
    
    #region Playback
    
    /// <summary>
    /// Play sound effect.
    /// </summary>
    /// <param name="clip">Audio clip</param>
    /// <param name="volumeScale">Volume scale (0-1)</param>
    /// <param name="pitch">Pitch (0.5-2)</param>
    /// <param name="position">3D position (optional)</param>
    public void PlaySFX(AudioClip clip, float volumeScale = 1f, float pitch = 1f, Vector3? position = null)
    {
        if (clip == null)
            return;
        
        AudioSource source = GetAvailableAudioSource();
        if (source == null)
        {
            Debug.LogWarning("No available audio source");
            return;
        }
        
        source.clip = clip;
        source.volume = masterVolume * sfxVolume * volumeScale;
        source.pitch = pitch;
        
        if (position.HasValue)
        {
            source.transform.position = position.Value;
            source.spatialBlend = 1f;
        }
        else
        {
            source.spatialBlend = 0f;
        }
        
        source.Play();
    }
    
    /// <summary>
    /// Play sound effect by name.
    /// </summary>
    /// <param name="clipName">Audio clip name in Resources</param>
    /// <param name="volumeScale">Volume scale</param>
    public void PlaySFX(string clipName, float volumeScale = 1f)
    {
        AudioClip clip = LoadAudioClip(clipName);
        if (clip != null)
        {
            PlaySFX(clip, volumeScale);
        }
    }
    
    /// <summary>
    /// Play one-shot sound effect.
    /// </summary>
    /// <param name="clip">Audio clip</param>
    /// <param name="volumeScale">Volume scale</param>
    public void PlayOneShot(AudioClip clip, float volumeScale = 1f)
    {
        if (clip == null)
            return;
        
        AudioSource source = GetAvailableAudioSource();
        if (source != null)
        {
            source.PlayOneShot(clip, masterVolume * sfxVolume * volumeScale);
        }
    }
    
    /// <summary>
    /// Stop all sounds.
    /// </summary>
    public void StopAll()
    {
        foreach (AudioSource source in audioSourcePool)
        {
            if (source.isPlaying)
            {
                source.Stop();
            }
        }
    }
    
    #endregion
    
    #region Volume Control
    
    /// <summary>
    /// Set master volume.
    /// </summary>
    /// <param name="volume">Volume (0-1)</param>
    public void SetMasterVolume(float volume)
    {
        masterVolume = Mathf.Clamp01(volume);
        UpdateAllVolumes();
    }
    
    /// <summary>
    /// Set SFX volume.
    /// </summary>
    /// <param name="volume">Volume (0-1)</param>
    public void SetSFXVolume(float volume)
    {
        sfxVolume = Mathf.Clamp01(volume);
        UpdateAllVolumes();
    }
    
    /// <summary>
    /// Set music volume.
    /// </summary>
    /// <param name="volume">Volume (0-1)</param>
    public void SetMusicVolume(float volume)
    {
        musicVolume = Mathf.Clamp01(volume);
        UpdateAllVolumes();
    }
    
    private void UpdateAllVolumes()
    {
        foreach (AudioSource source in audioSourcePool)
        {
            if (source.isPlaying)
            {
                // Update playing sources (simplified)
                source.volume = masterVolume * sfxVolume;
            }
        }
    }
    
    #endregion
    
    #region Pool Management
    
    private AudioSource GetAvailableAudioSource()
    {
        // Find first non-playing source
        AudioSource available = audioSourcePool.FirstOrDefault(s => !s.isPlaying);
        
        if (available == null)
        {
            // All sources busy, return least recently used
            available = audioSourcePool[0];
        }
        
        return available;
    }
    
    #endregion
    
    #region Resource Loading
    
    private AudioClip LoadAudioClip(string clipName)
    {
        // Check cache first
        if (audioClipCache.ContainsKey(clipName))
        {
            return audioClipCache[clipName];
        }
        
        // Load from Resources
        AudioClip clip = Resources.Load<AudioClip>($"Audio/{clipName}");
        
        if (clip != null)
        {
            audioClipCache[clipName] = clip;
        }
        else
        {
            Debug.LogWarning($"Audio clip not found: {clipName}");
        }
        
        return clip;
    }
    
    #endregion
}
