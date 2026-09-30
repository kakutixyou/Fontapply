import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { electronAPI } from '../api/electronAPI';
import { useDesignStore } from '../store/designStore';
import './Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();
  // 状態管理（Zustand Store）から必要な機能を取得
  const { projects, setProjects, setCurrentProject, setError, error } = useDesignStore();
  
  // コンポーネント内のローカル状態
  const [isLoading, setIsLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');

  // プロジェクト一覧を取得する関数
  const loadProjects = async () => {
    try {
      setIsLoading(true);
      // Electron側（SQLite）から本物のデータを取得
      const records = await electronAPI.projects.list();
      setProjects(records);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoading(false);
    }
  };

  // 画面を開いた時に一度だけデータを読み込む
  useEffect(() => {
    void loadProjects();
  }, []);

  // 新規プロジェクト作成処理
  const handleCreate = async () => {
    if (!name.trim()) return;

    try {
      const project = await electronAPI.projects.create({ name: name.trim() });
      setCurrentProject(project);
      setShowCreate(false);
      setName('');
      await loadProjects();
      // 作成後、そのプロジェクトの編集画面へ遷移
      navigate(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  // プロジェクト削除処理
  const handleDelete = async (projectId: string) => {
    try {
      await electronAPI.projects.delete(projectId);
      await loadProjects(); // 削除後に一覧を再取得して画面を更新
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <section className="dashboard-page">
      {/* ── ヘッダー部分 ── */}
      <div className="dashboard-page__header">
        <div>
          <p className="section-label">Projects</p>
          <h1>ダッシュボード</h1>
          <p>デザイン変換・フォント生成プロジェクトを管理します。</p>
        </div>
        <div className="dashboard-page__actions">
          <button type="button" onClick={() => navigate('/converter')}>
            クイック変換
          </button>
          <button type="button" onClick={() => setShowCreate(true)}>
            ➕ 新規プロジェクト
          </button>
        </div>
      </div>

      {/* エラー表示 */}
      {error && <p className="page-error" style={{ color: '#ff5050' }}>{error}</p>}

      {/* ── メインコンテンツ部分 ── */}
      {isLoading ? (
        <div className="dashboard-empty">読み込み中...</div>
      ) : projects.length > 0 ? (
        <div className="dashboard-grid">
          {projects.map((project) => (
            <article key={project.id} className="dashboard-card">
              <div>
                <h3>{project.name}</h3>
                <p style={{ fontSize: '0.9rem', color: '#888' }}>
                  {/* 画像がない場合はプレースホルダーテキストを表示 */}
                  {project.image_path ? '🖼️ 画像あり' : '📄 画像未登録'}
                </p>
                <p className="dashboard-card__meta">
                  作成日: {new Date(project.created_at).toLocaleDateString('ja-JP')}
                </p>
              </div>
              <div className="dashboard-card__actions">
                <button type="button" onClick={() => navigate(`/projects/${project.id}`)}>
                  開く
                </button>
                <button 
                  type="button" 
                  className="button--ghost" 
                  onClick={() => void handleDelete(project.id)}
                >
                  削除
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="dashboard-empty" style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>
          <p>まだプロジェクトはありません。</p>
          <p>右上の「新規プロジェクト」から作成して始めましょう！</p>
        </div>
      )}

      {/* ── 新規作成モーダル ── */}
      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          {/* モーダルの中身をクリックしても閉じないようにする */}
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h2>新規プロジェクト</h2>
            <input 
              value={name} 
              onChange={(event) => setName(event.target.value)} 
              placeholder="プロジェクト名を入力..." 
              autoFocus 
              onKeyDown={(e) => {
                // Enterキーでも作成できるようにする
                if (e.key === 'Enter') void handleCreate();
              }}
            />
            <div className="modal-card__actions">
              <button type="button" className="button--ghost" onClick={() => setShowCreate(false)}>
                キャンセル
              </button>
              <button type="button" onClick={() => void handleCreate()}>
                作成
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}