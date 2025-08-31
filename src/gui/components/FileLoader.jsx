import React, { useState } from 'react';
import { Radio, Upload, AlertCircle, Loader, FolderOpen } from 'lucide-react';

const FileLoader = ({ onDataLoaded }) => {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, fileName: '' });
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileInput = async (files) => {
    if (!files || files.length === 0) return;

    setLoading(true);
    setError(null);
    
    const jsonFiles = Array.from(files).filter(file => 
      file.name.toLowerCase().endsWith('.json')
    );

    if (jsonFiles.length === 0) {
      setError('Keine JSON-Dateien ausgewählt.');
      setLoading(false);
      return;
    }

    const loadedData = [];
    setProgress({ current: 0, total: jsonFiles.length, fileName: '' });

    for (let i = 0; i < jsonFiles.length; i++) {
      const file = jsonFiles[i];
      setProgress({ current: i + 1, total: jsonFiles.length, fileName: file.name });

      try {
        const text = await file.text();
        const jsonData = JSON.parse(text);
        
        if (jsonData.sender && jsonData.segments) {
          loadedData.push(jsonData);
        }
      } catch (fileError) {
        console.warn(`Fehler beim Laden von ${file.name}:`, fileError);
      }

      await new Promise(resolve => setTimeout(resolve, 50));
    }

    if (loadedData.length > 0) {
      onDataLoaded(loadedData);
    } else {
      setError('Keine gültigen Radio-Summary-Dateien gefunden.');
    }

    setLoading(false);
    setProgress({ current: 0, total: 0, fileName: '' });
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    handleFileInput(e.dataTransfer.files);
  };

  const loadDemoData = () => {
    const stations = ['SWR1', 'SWR3', 'WDR2'];
    const segmentTypes = ['news', 'music', 'weather', 'traffic', 'interview', 'sport'];
    const topicsPool = ['Bahn', 'Wetter', 'Ukraine', 'Trump', 'Putin', 'Plastikmüll', 'Wirtschaft', 'Kultur', 'Sport'];

    const days = 12;
    const demoData = [];
    for (let d = 0; d < days; d++) {
      const day = new Date();
      day.setDate(day.getDate() - d);
      const dayStr = day.toISOString().slice(0,10);

      stations.forEach((station) => {
        for (let h = 8; h < 11; h++) {
          const hourStart = `${dayStr}T${String(h).padStart(2,'0')}:00:00`;
          const hourEnd = `${dayStr}T${String(h+1).padStart(2,'0')}:00:00`;

          const segments = [];
          const segCount = 6 + Math.floor(Math.random() * 6);
          for (let s = 0; s < segCount; s++) {
            const type = segmentTypes[Math.floor(Math.random() * segmentTypes.length)];
            const startMinute = Math.floor((60 / segCount) * s);
            const start = `${dayStr}T${String(h).padStart(2,'0')}:${String(startMinute).padStart(2,'0')}:00`;
            const end = `${dayStr}T${String(h).padStart(2,'0')}:${String(Math.min(startMinute + 5,59)).padStart(2,'0')}:00`;
            const topics = [];
            const tCount = 1 + Math.floor(Math.random() * 3);
            for (let t = 0; t < tCount; t++) topics.push(topicsPool[Math.floor(Math.random() * topicsPool.length)]);

            segments.push({
              type,
              title: `${type.charAt(0).toUpperCase() + type.slice(1)} Segment ${s+1}`,
              topic: topics[0],
              start,
              end,
              speakers: (type === 'interview' ? ['Moderator A', 'Gast B'] : ['Moderator A']),
              summary: `${type} - kurze Zusammenfassung über ${topics.join(', ')}.`,
              topics
            });
          }

          demoData.push({
            sender: station,
            hour_start: hourStart,
            hour_end: hourEnd,
            show_title: `${station} Morgenshow ${dayStr}`,
            hosts: ['Moderator A'],
            main_topics: [topicsPool[Math.floor(Math.random() * topicsPool.length)]],
            news_topics: [topicsPool[Math.floor(Math.random() * topicsPool.length)]],
            weather_present: Math.random() > 0.5,
            traffic_present: Math.random() > 0.5,
            ads_present: Math.random() > 0.5,
            segments
          });
        }
      });
    }
    demoData.sort(() => Math.random() - 0.5);
    onDataLoaded(demoData);
  };

  const supportsFileSystemAccess = typeof window !== 'undefined' && 'showDirectoryPicker' in window;

  const loadFromDirectory = async () => {
    if (!supportsFileSystemAccess) {
      setError('Ihr Browser unterstützt die Ordner-Auswahl nicht. Bitte verwenden Sie Chrome oder Edge.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const directoryHandle = await window.showDirectoryPicker({ mode: 'read' });
      const jsonFiles = [];

      for await (const [name, handle] of directoryHandle.entries()) {
        if (handle.kind === 'file' && name.toLowerCase().endsWith('.json')) {
          jsonFiles.push({ name, handle });
        }
      }

      if (jsonFiles.length === 0) {
        setError('Keine JSON-Dateien im ausgewählten Ordner gefunden.');
        setLoading(false);
        return;
      }

      const loadedData = [];
      setProgress({ current: 0, total: jsonFiles.length, fileName: '' });

      for (let i = 0; i < jsonFiles.length; i++) {
        const { name, handle } = jsonFiles[i];
        setProgress({ current: i + 1, total: jsonFiles.length, fileName: name });

        try {
          const file = await handle.getFile();
          const text = await file.text();
          const jsonData = JSON.parse(text);

          if (jsonData.sender && jsonData.segments) {
            loadedData.push(jsonData);
          }
        } catch (fileError) {
          console.warn(`Fehler beim Laden von ${name}:`, fileError);
        }
      }

      if (loadedData.length > 0) {
        onDataLoaded(loadedData);
      } else {
        setError('Keine gültigen Radio-Summary-Dateien gefunden.');
      }
    } catch (err) {
      if (err.name !== 'AbortError') setError(`Fehler beim Laden: ${err.message}`);
    } finally {
      setLoading(false);
      setProgress({ current: 0, total: 0, fileName: '' });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-lg w-full">
        <div className="text-center mb-8">
          <Radio className="w-16 h-16 text-blue-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Radio Summary Analysis</h1>
          <p className="text-gray-600">Laden Sie Ihre JSON-Dateien, um zu beginnen</p>
        </div>

        {loading ? (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <Loader className="w-8 h-8 text-blue-600 mx-auto mb-4 animate-spin" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Lade Dateien...</h3>
            <p className="text-gray-600 mb-4">{progress.current} von {progress.total} Dateien</p>
            {progress.fileName && (
              <p className="text-sm text-gray-500 mb-4 truncate">Aktuelle Datei: {progress.fileName}</p>
            )}
            <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
              <div className="bg-blue-600 h-2 rounded-full transition-all duration-300" style={{ width: `${progress.total > 0 ? (progress.current / progress.total) * 100 : 0}%` }} />
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className={`bg-white rounded-lg shadow-lg p-8 border-2 border-dashed transition-colors ${dragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300'}`} onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}>
              <div className="text-center">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">JSON-Dateien auswählen</h3>
                <p className="text-gray-600 mb-4">Ziehen Sie Ihre Radio-Summary JSON-Dateien hierher oder klicken Sie zum Auswählen</p>
                <input type="file" multiple accept=".json" onChange={(e) => handleFileInput(e.target.files)} className="hidden" id="fileInput" />
                <label htmlFor="fileInput" className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium cursor-pointer inline-block">Dateien auswählen</label>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-yellow-800 font-medium text-sm">Demo-Modus</h4>
                  <p className="text-yellow-700 text-sm mt-1">Testen Sie die App mit Beispiel-Daten</p>
                </div>
                <button onClick={loadDemoData} className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors text-sm">Demo starten</button>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="text-center">
                <h4 className="text-blue-800 font-medium text-sm mb-2">Unterstützte Dateien</h4>
                <p className="text-blue-700 text-sm">JSON-Dateien von WDR2, SWR1, SWR3 mit Radio-Summary-Daten</p>
                <p className="text-blue-700 text-sm mt-1">Beispiel: wdr2_20250814_23.json, swr3_20250814_22.json</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileLoader;
