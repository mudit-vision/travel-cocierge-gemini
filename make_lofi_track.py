"""Synthesize an upbeat lo-fi background music track in WAV format."""

import numpy as np
from scipy.io import wavfile

SAMPLE_RATE = 44100
BPM = 88
BEAT_DUR = 60.0 / BPM  # ~0.6818s per beat
BAR_DUR = BEAT_DUR * 4
TOTAL_DURATION = 45.0  # 45 seconds to cover demo video


def generate_kick(dur, sr=SAMPLE_RATE):
    t = np.linspace(0, dur, int(sr * dur), False)
    freq = 60 * np.exp(-t * 25) + 30
    env = np.exp(-t * 12)
    kick = np.sin(2 * np.pi * freq * t) * env
    return kick


def generate_snare(dur, sr=SAMPLE_RATE):
    t = np.linspace(0, dur, int(sr * dur), False)
    noise = np.random.uniform(-1, 1, len(t))
    tone = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 20)
    noise_env = np.exp(-t * 15)
    snare = 0.6 * tone + 0.4 * noise * noise_env
    return snare


def generate_hihat(dur, sr=SAMPLE_RATE, accent=1.0):
    t = np.linspace(0, dur, int(sr * dur), False)
    noise = np.random.uniform(-1, 1, len(t))
    env = np.exp(-t * 40)
    # Simple high-pass
    hihat = np.diff(noise, prepend=0) * env * accent
    return hihat


def rhodes_chord(freqs, dur, sr=SAMPLE_RATE):
    t = np.linspace(0, dur, int(sr * dur), False)
    signal = np.zeros_like(t)
    for f in freqs:
        # Sine + 2nd harmonic for warm electric piano timbre
        wave = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 2 * t)
        env = np.exp(-t * 2.5) * (1.0 - np.exp(-t * 50))
        signal += wave * env
    return signal / len(freqs)


def main():
    total_samples = int(SAMPLE_RATE * TOTAL_DURATION)
    audio = np.zeros(total_samples, dtype=np.float32)

    # Chords (Fmaj7, Em7, Dm7, Cmaj7)
    f_maj7 = [174.61, 220.00, 261.63, 329.63]
    e_m7 = [164.81, 196.00, 246.94, 293.66]
    d_m7 = [146.83, 174.61, 220.00, 261.63]
    c_maj7 = [130.81, 164.81, 196.00, 246.94]
    chords = [f_maj7, e_m7, d_m7, c_maj7]
    roots = [87.31, 82.41, 73.42, 65.41]  # Bass root notes

    # Generate 4-bar loop and repeat to fill total duration
    num_bars = int(np.ceil(TOTAL_DURATION / BAR_DUR))

    for bar_idx in range(num_bars):
        bar_start_time = bar_idx * BAR_DUR
        bar_start_sample = int(bar_start_time * SAMPLE_RATE)
        chord = chords[bar_idx % 4]
        root_freq = roots[bar_idx % 4]

        # 1. Play Rhodes Chord on beat 1 and beat 2.5
        c_audio = rhodes_chord(chord, BAR_DUR * 0.9)
        c_len = min(len(c_audio), total_samples - bar_start_sample)
        if c_len > 0:
            audio[bar_start_sample : bar_start_sample + c_len] += c_audio[:c_len] * 0.45

        # 2. Bass note
        t_bass = np.linspace(0, BAR_DUR, int(SAMPLE_RATE * BAR_DUR), False)
        bass_wave = np.sin(2 * np.pi * root_freq * t_bass) * np.exp(-t_bass * 1.5)
        b_len = min(len(bass_wave), total_samples - bar_start_sample)
        if b_len > 0:
            audio[bar_start_sample : bar_start_sample + b_len] += bass_wave[:b_len] * 0.35

        # 3. Drum Pattern (4 beats per bar)
        # Kick on beat 1 and beat 3
        # Snare on beat 2 and beat 4
        # Hi-hat on every 8th note
        beat_samples = int(BEAT_DUR * SAMPLE_RATE)
        kick_sound = generate_kick(BEAT_DUR)
        snare_sound = generate_snare(BEAT_DUR)

        for beat in range(4):
            beat_sample_idx = bar_start_sample + int(beat * BEAT_DUR * SAMPLE_RATE)

            # Kick on 1 and 2.5 (swing)
            if beat in [0, 2]:
                k_len = min(len(kick_sound), total_samples - beat_sample_idx)
                if k_len > 0 and beat_sample_idx < total_samples:
                    audio[beat_sample_idx : beat_sample_idx + k_len] += kick_sound[:k_len] * 0.6

            # Snare on 2 and 4
            if beat in [1, 3]:
                s_len = min(len(snare_sound), total_samples - beat_sample_idx)
                if s_len > 0 and beat_sample_idx < total_samples:
                    audio[beat_sample_idx : beat_sample_idx + s_len] += snare_sound[:s_len] * 0.5

            # Hi-hats (2 per beat = 8th notes)
            for sub in [0, 0.5]:
                hh_sound = generate_hihat(BEAT_DUR * 0.4, accent=1.0 if sub == 0 else 0.6)
                hh_sample_idx = beat_sample_idx + int(sub * BEAT_DUR * SAMPLE_RATE)
                hh_len = min(len(hh_sound), total_samples - hh_sample_idx)
                if hh_len > 0 and hh_sample_idx < total_samples:
                    audio[hh_sample_idx : hh_sample_idx + hh_len] += hh_sound[:hh_len] * 0.15

    # 4. Add subtle vinyl crackle
    vinyl = np.random.normal(0, 0.008, total_samples).astype(np.float32)
    audio += vinyl

    # Normalize audio to prevent clipping
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = (audio / max_val) * 0.85

    # Save as 16-bit PCM WAV
    audio_int16 = (audio * 32767).astype(np.int16)
    out_path = "/config/.gemini/antigravity/scratch/travel-concierge/lofi_music.wav"
    wavfile.write(out_path, SAMPLE_RATE, audio_int16)
    print(f"LOFI MUSIC GENERATED SUCCESSFULLY: {out_path}")


if __name__ == "__main__":
    main()
