import React, { useState, useMemo } from 'react';
import FileLoader from './components/FileLoader';
import TopNewsOfDay from './components/TopNews';
import { Search, Radio, Clock, Users, Mic, BarChart3, Clock as ClockIcon, TrendingUp } from 'lucide-react';

const RadioSummaryApp = () => {
  const [data, setData] = useState([]);
  const [appState, setAppState] = useState('loading');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStation, setSelectedStation] = useState('all');
  const [activeTab, setActiveTab] = useState('dashboard');

  const [dateStart, setDateStart] = useState('');
  const [dateEnd, setDateEnd] = useState('');
  const [selectedType, setSelectedType] = useState('all');

  const handleDataLoaded = (loadedData) => { 
    const normalizeSender = (raw) => {
      if (!raw) return raw;
      const s = String(raw).toLowerCase();
      const cleaned = s.replace(/[^a-z0-9]/g, '');
      if (cleaned.startsWith('swr1')) return 'SWR1';
      if (cleaned.startsWith('swr3')) return 'SWR3';
      if (cleaned.startsWith('wdr2')) return 'WDR2';

      if (s.includes('swr 1') || s.includes('swr1') || s.includes('swr1rheinland') || s.includes('swr 1 rheinland')) return 'SWR1';
      if (s.includes('swr 3') || s.includes('swr3')) return 'SWR3';
      if (s.includes('wdr2') || s.includes('wdr 2')) return 'WDR2';
      return raw;
    };

    const normalized = (loadedData || []).map(item => ({ ...item, sender: normalizeSender(item.sender) }));
    setData(normalized); setAppState('loaded'); 
  };

  const stats = useMemo(() => {
    const allSegments = data.flatMap(d => d.segments || []);
    const segmentTypes = [...new Set(allSegments.map(s => s.type))];
    return {
      totalHours: data.length,
      totalSegments: allSegments.length,
      stations: [...new Set(data.map(d => d.sender))].length,
      avgSegmentsPerHour: Math.round(allSegments.length / Math.max(data.length, 1) * 10) / 10,
      segmentTypes,
      typeDistribution: segmentTypes.map(type => ({ type, count: allSegments.filter(s => s.type === type).length })),
      dateRange: data.length > 0 ? { start: new Date(Math.min(...data.map(d => new Date(d.hour_start)))), end: new Date(Math.max(...data.map(d => new Date(d.hour_start)))) } : null
    };
  }, [data]);
  const rawQ = (searchTerm || '').trim();
  const normalize = (s) => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/ß/g, 'ss').toLowerCase();
  const q = normalize(rawQ);
  const terms = q ? q.split(/\s+/) : [];

  const filteredData = useMemo(() => {
    return data.filter(item => {
      const matchesStation = selectedStation === 'all' || item.sender === selectedStation;

      if (dateStart || dateEnd) {
        if (!item.hour_start) return false;
        const itemDay = item.hour_start.slice(0, 10);
        if (dateStart && itemDay < dateStart) return false;
        if (dateEnd && itemDay > dateEnd) return false;
      }

  if (!q) return matchesStation;

  const parts = [];
  if (item.sender) parts.push(String(item.sender));
  if (item.show_title) parts.push(String(item.show_title));
      if (item.main_topics && Array.isArray(item.main_topics)) parts.push(...item.main_topics);
      if (item.news_topics && Array.isArray(item.news_topics)) parts.push(...item.news_topics);
      if (item.hosts && Array.isArray(item.hosts)) parts.push(...item.hosts);

      (item.segments || []).forEach(seg => {
        if (seg.title) parts.push(seg.title);
        if (seg.summary) parts.push(seg.summary);
        if (seg.topic) parts.push(seg.topic);
  if (seg.speakers && Array.isArray(seg.speakers)) parts.push(...seg.speakers);
        if (seg.topics && Array.isArray(seg.topics)) parts.push(...seg.topics);
      });

      const hay = normalize(parts.filter(Boolean).join(' '));

      const matchesSearch = terms.length === 0 ? true : terms.some(t => hay.includes(t));

      return matchesStation && matchesSearch;
    });
  }, [data, selectedStation, dateStart, dateEnd, searchTerm]);

  const timelineData = useMemo(() => {
    if (!q) return filteredData;
  const mapped = filteredData.map(show => {
      const segs = (show.segments || []).filter(seg => {
  const parts = [];
  if (show.sender) parts.push(show.sender);
  if (show.show_title) parts.push(show.show_title);

        if (seg.title) parts.push(seg.title);
        if (seg.summary) parts.push(seg.summary);
        if (seg.topic) parts.push(seg.topic);
        if (seg.topics && Array.isArray(seg.topics)) parts.push(...seg.topics);
  if (seg.speakers && Array.isArray(seg.speakers)) parts.push(...seg.speakers);

        const hay = normalize(parts.filter(Boolean).join(' '));
        return terms.length === 0 ? true : terms.some(t => hay.includes(t));
      });
      return { ...show, segments: segs };
  }).filter(s => (s.segments || []).length > 0);
  return mapped;
  }, [filteredData, searchTerm]);

  const filteredSegments = useMemo(() => filteredData.flatMap(d => (d.segments || []).map(s => ({ ...s, station: d.sender, show_title: d.show_title, date: d.hour_start }))).filter(s => selectedType === 'all' ? true : s.type === selectedType), [filteredData, selectedType]);

  const stationOptions = useMemo(() => {
    return [...new Set(data.map(d => d.sender).filter(Boolean))].sort();
  }, [data]);

  const filteredStats = useMemo(() => {
    const allSegments = filteredData.flatMap(d => d.segments || []);
    const segmentTypes = [...new Set(allSegments.map(s => s.type))];
    return {
      totalHours: filteredData.length,
      totalSegments: allSegments.length,
      stations: [...new Set(filteredData.map(d => d.sender))].length,
      avgSegmentsPerHour: Math.round(allSegments.length / Math.max(filteredData.length, 1) * 10) / 10,
      segmentTypes,
      typeDistribution: segmentTypes.map(type => ({ type, count: allSegments.filter(s => s.type === type).length }))
    };
  }, [filteredData]);

  const activeStats = (dateStart || dateEnd || selectedStation !== 'all' || searchTerm) ? filteredStats : stats;

  if (appState === 'loading') return <FileLoader onDataLoaded={handleDataLoaded} />;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <Radio className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Radio Summary Analysis</h1>
                {stats.dateRange && (
                  <p className="text-sm text-gray-600">{stats.dateRange.start.toLocaleDateString('de-DE')} - {stats.dateRange.end.toLocaleDateString('de-DE')}</p>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <button onClick={() => setAppState('loading')} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">Neue Dateien laden</button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <section className="mb-6">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="w-5 h-5 text-gray-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Suche in Titeln, Themen und Zusammenfassungen..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <select value={selectedStation} onChange={(e) => setSelectedStation(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-md">
              <option value="all">Alle Sender</option>
              {stationOptions.map(s => <option key={s} value={s}>{s}</option>)}
            </select>

            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-600">Von</label>
              <input type="date" value={dateStart} onChange={(e) => setDateStart(e.target.value)} className="border px-2 py-1 rounded-md" />
              <label className="text-sm text-gray-600">Bis</label>
              <input type="date" value={dateEnd} onChange={(e) => setDateEnd(e.target.value)} className="border px-2 py-1 rounded-md" />
              <button onClick={() => { setDateStart(''); setDateEnd(''); }} className="text-sm text-gray-500 hover:text-gray-700">Zurücksetzen</button>
            </div>
          </div>
        </section>

        <section className="mb-6">
          <nav className="flex space-x-6">
            {[{ id: 'dashboard', label: 'Dashboard', icon: BarChart3 }, { id: 'timeline', label: 'Timeline', icon: ClockIcon }, { id: 'segments', label: 'Segmente', icon: Mic }, { id: 'topics', label: 'Themen', icon: TrendingUp }].map(({ id, label, icon: Icon }) => (
              <button key={id} onClick={() => setActiveTab(id)} className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${activeTab === id ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}>
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </section>

        <section>
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2 space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="bg-white p-6 rounded-lg shadow">
                      <div className="flex items-center">
                        <Radio className="w-8 h-8 text-blue-600" />
                        <div className="ml-4">
                          <p className="text-sm text-gray-600">Gesamt Stunden</p>
                          <p className="text-2xl font-semibold">{activeStats.totalHours}</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white p-6 rounded-lg shadow">
                      <div className="flex items-center">
                        <Mic className="w-8 h-8 text-green-600" />
                        <div className="ml-4">
                          <p className="text-sm text-gray-600">Segmente</p>
                          <p className="text-2xl font-semibold">{activeStats.totalSegments}</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white p-6 rounded-lg shadow">
                      <div className="flex items-center">
                        <Clock className="w-8 h-8 text-purple-600" />
                        <div className="ml-4">
                          <p className="text-sm text-gray-600">⌀ Segmente/Stunde</p>
                          <p className="text-2xl font-semibold">{activeStats.avgSegmentsPerHour}</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white p-6 rounded-lg shadow">
                      <div className="flex items-center">
                        <Users className="w-8 h-8 text-orange-600" />
                        <div className="ml-4">
                          <p className="text-sm text-gray-600">Sender</p>
                          <p className="text-2xl font-semibold">{activeStats.stations}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Segmenttypen Verteilung</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {activeStats.typeDistribution.map(td => (
                        <div key={td.type} className="text-center p-4 bg-gray-50 rounded-lg">
                          <div className="text-2xl font-bold">{td.count}</div>
                          <div className="text-sm text-gray-600 capitalize">{td.type}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <aside className="md:col-span-1">
                  <TopNewsOfDay data={data} />
                </aside>

              </div>
            </div>
          )}

          {activeTab === 'timeline' && (
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h3 className="text-lg font-semibold">Sendungszeitleiste</h3>
                <p className="text-sm text-gray-600">Chronologische Übersicht aller Segmente</p>
              </div>

              <div className="p-6">
                <div className="space-y-6">
                  {timelineData.map((show) => (
                    <div key={`${show.sender}-${show.hour_start}`} className="border-l-4 border-blue-500 pl-6 relative">
                      <div className="absolute -left-2 top-0 w-4 h-4 bg-blue-500 rounded-full" />
                      <div className="mb-2 flex items-center justify-between">
                        <div>
                          <h4 className="font-semibold text-gray-900">{show.sender.toUpperCase()} - {show.show_title}</h4>
                          <p className="text-sm text-gray-600">{new Date(show.hour_start).toLocaleString('de-DE')}</p>
                        </div>
                        {q && (
                          <div className="ml-4">
                            <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">{(show.segments || []).length} Treffer</span>
                          </div>
                        )}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {show.segments?.slice(0, 12).map((segment) => (
                          <div key={segment.start || `${show.sender}-${segment.title?.slice(0,10)}` } className="bg-gray-50 p-3 rounded border">
                            <div className="flex items-center space-x-2 mb-2">
                              <span className="text-xs font-medium text-gray-600 capitalize">{segment.type}</span>
                            </div>
                            <p className="text-sm font-medium text-gray-900 mb-1">{segment.title}</p>
                            <p className="text-xs text-gray-600">{segment.summary?.substring(0, 140)}{segment.summary && segment.summary.length > 140 ? '...' : ''}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'segments' && (
            <div className="space-y-4">
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Gefunden: {filteredSegments.length} Segmente</p>
              </div>

              {filteredSegments.map((segment) => (
                <div key={`${segment.station}-${segment.start}`} className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">{segment.station?.toUpperCase()}</span>
                        <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs font-medium rounded capitalize">{segment.type}</span>
                        <span className="text-xs text-gray-500">{new Date(segment.start).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>

                      <h3 className="text-lg font-semibold text-gray-900 mb-2">{segment.title}</h3>
                      <p className="text-gray-700 mb-3">{segment.summary}</p>

                      {segment.speakers && segment.speakers.length > 0 && (
                        <div className="mb-2">
                          <span className="text-sm font-medium text-gray-600">Sprecher: </span>
                          <span className="text-sm text-gray-700">{segment.speakers.join(', ')}</span>
                        </div>
                      )}

                      {segment.topics && segment.topics.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {segment.topics.map((topic) => (
                            <span key={topic} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">{topic}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'topics' && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-6">Themen-Analyse</h3>

              <div className="space-y-6">
                {filteredData.map((show) => (
                  <div key={`${show.sender}-${show.hour_start}`} className="border-b border-gray-200 pb-6 last:border-b-0">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-semibold text-gray-900">{show.sender.toUpperCase()} - {new Date(show.hour_start).toLocaleDateString('de-DE')}</h4>
                    </div>

                    <div className="mb-4">
                      <h5 className="text-sm font-medium text-gray-700 mb-2">Hauptthemen:</h5>
                      <div className="flex flex-wrap gap-2">
                        {show.main_topics?.map((topic) => (
                          <span key={topic} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">{topic}</span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h5 className="text-sm font-medium text-gray-700 mb-2">Nachrichten-Themen:</h5>
                      <div className="flex flex-wrap gap-2">
                        {show.news_topics?.map((topic) => (
                          <span key={topic} className="px-3 py-1 bg-red-100 text-red-800 text-sm rounded-full">{topic}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default RadioSummaryApp;
