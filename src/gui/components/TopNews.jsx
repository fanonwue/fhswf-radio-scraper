import React, { useMemo } from 'react';
import { Newspaper, Users, Star, ArrowRight } from 'lucide-react';

const TopNewsOfDay = ({ data }) => {
  const { topNews, counts } = useMemo(() => {
    const importantTopicsRegex = /politik|international|wirtschaft|bahn|ukraine|trump|putin|korrupt|skandal|gericht|regierung/i;

    const newsSegments = data.flatMap(show =>
      (show.segments || [])
        .filter(segment =>
          segment.type === 'news' &&
          !segment.topic?.toLowerCase().includes('wetter') &&
          !segment.topic?.toLowerCase().includes('verkehr') &&
          segment.summary && segment.summary.length > 30
        )
        .map(segment => {
          let score = 0;
          const durationMs = (new Date(segment.end) - new Date(segment.start)) || 0;
          score += Math.min(durationMs / (1000 * 60), 10);

          const summary = (segment.summary || '').toLowerCase();
          if (importantTopicsRegex.test(summary) || (segment.topics || []).some(t => importantTopicsRegex.test(t))) score += 8;

          const title = (segment.title || '').toLowerCase();
          if (importantTopicsRegex.test(title)) score += 6;

          if (show.main_topics && show.main_topics.some(mt => importantTopicsRegex.test(mt))) score += 3;

          if (segment.speakers && segment.speakers.length > 0) score += 2;

          score += Math.min((segment.summary?.length || 0) / 50, 6);

          return {
            ...segment,
            station: show.sender,
            date: show.hour_start,
            show_title: show.show_title,
            importance: Math.round(score * 10) / 10
          };
        })
    );

    const counts = newsSegments.reduce((acc, s) => { acc[s.station] = (acc[s.station] || 0) + 1; return acc; }, {});

    const topNews = newsSegments.sort((a, b) => (b.importance || 0) - (a.importance || 0)).slice(0, 5);
    return { topNews, counts };
  }, [data]);

  const formatTime = (dateString) => new Date(dateString).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  const formatDate = (dateString) => new Date(dateString).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });

  if (topNews.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-3 mb-4">
          <Newspaper className="w-6 h-6 text-red-600" />
          <h3 className="text-lg font-semibold text-gray-900">Top 5 Nachrichten des Tages</h3>
        </div>
        <p className="text-gray-500">Keine Nachrichten gefunden.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Newspaper className="w-6 h-6 text-red-600" />
            <h3 className="text-lg font-semibold text-gray-900">Top 5 Nachrichten des Tages</h3>
          </div>
          <span className="text-sm text-gray-500">Nach Relevanz sortiert</span>
        </div>
      </div>

      <div className="p-4 border-b bg-gray-50">
        <div className="flex flex-wrap gap-2">
          {Object.entries(counts).length === 0 ? (
            <span className="text-sm text-gray-500">Keine qualifizierten Meldungen</span>
          ) : (
            Object.entries(counts).map(([station, c]) => (
              <div key={station} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full font-medium">{station}: {c}</div>
            ))
          )}
        </div>
      </div>

      <div className="p-6">
        <div className="space-y-4">
          {topNews.map((news, index) => (
            <div key={`${news.station}-${news.start || index}`} className="flex items-start space-x-4 p-4 bg-gray-50 rounded-lg">
              <div className="flex-shrink-0"><div className="flex items-center justify-center w-8 h-8 bg-red-600 text-white rounded-full font-semibold text-sm">{index + 1}</div></div>
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="px-2.5 py-0.5 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">{news.station?.toUpperCase()}</span>
                  <span className="text-xs text-gray-500">{formatDate(news.date)} • {formatTime(news.start)}</span>
                  {news.importance > 15 && <Star className="w-4 h-4 text-yellow-500 fill-current" />}
                </div>
                <h4 className="text-base font-semibold text-gray-900 mb-2">{news.title}</h4>
                <p className="text-sm text-gray-700 mb-3">{news.summary}</p>
                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-1">{(news.topics?.slice(0,3) || []).map((t,i) => <span key={i} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded font-medium">{t}</span>)}</div>
                  {news.speakers && news.speakers.length > 0 && <div className="text-xs text-gray-500"><Users className="w-3 h-3 inline mr-1" />{news.speakers.slice(0,2).join(', ')}</div>}
                </div>
              </div>
              <ArrowRight className="w-5 h-5 text-gray-400 mt-4" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TopNewsOfDay;
