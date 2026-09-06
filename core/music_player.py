"""Музыкальный плеер"""

from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from utils.logger import logger


class MusicPlayer:
    def __init__(self):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        self.current_playlist = []
        self.current_index = -1
        self.is_playing = False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        
        # Сигналы для внешнего использования
        self.position_changed_callback = None
        self.state_changed_callback = None
        
        # Подключение сигналов
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)
    
    def set_track(self, index):
        """Установка трека для воспроизведения"""
        if 0 <= index < len(self.current_playlist):
            self.current_index = index
            track = self.current_playlist[index]
            
            logger.info(f"Воспроизведение: {track['artist']} - {track['title']}")
            
            self.player.setSource(QUrl(track['url']))
            self.player.play()
            self.is_playing = True
            self.timer.start(1000)
            
            return track
        return None
    
    def play(self):
        self.player.play()
        self.is_playing = True
    
    def pause(self):
        self.player.pause()
        self.is_playing = False
    
    def toggle(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
            return False
        else:
            self.play()
            return True
    
    def stop(self):
        self.player.stop()
        self.is_playing = False
        self.timer.stop()
    
    def next(self):
        if self.current_index < len(self.current_playlist) - 1:
            self.current_index += 1
            return self.set_track(self.current_index)
        return None
    
    def previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            return self.set_track(self.current_index)
        return None
    
    def set_playlist(self, playlist):
        """Установка нового плейлиста"""
        self.current_playlist = playlist
        self.current_index = -1
    
    def set_volume(self, volume):
        """Установка громкости (0-100)"""
        self.audio_output.setVolume(volume / 100)
    
    def get_volume(self):
        return int(self.audio_output.volume() * 100)
    
    def get_position(self):
        return self.player.position()
    
    def get_duration(self):
        return self.player.duration()
    
    def get_progress(self):
        duration = self.get_duration()
        if duration > 0:
            return int((self.get_position() / duration) * 100)
        return 0
    
    def update_progress(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            if self.position_changed_callback:
                self.position_changed_callback(self.get_progress())
    
    def _on_position_changed(self, position):
        if self.position_changed_callback:
            self.position_changed_callback(self.get_progress())
    
    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.is_playing = False
            self.timer.stop()
            if self.state_changed_callback:
                self.state_changed_callback("stopped")
    
    def get_current_track(self):
        if 0 <= self.current_index < len(self.current_playlist):
            return self.current_playlist[self.current_index]
        return None
    
    def get_current_track_index(self):
        return self.current_index
    
    def get_playlist(self):
        return self.current_playlist
    
    def get_playlist_count(self):
        return len(self.current_playlist)
    
    def is_playing_state(self):
        return self.is_playing
