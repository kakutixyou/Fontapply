
import { useEffect, useState } from 'react';

import { useNavigate } from 'react-router-dom';
import { electronAPI } from '../../api/electronAPI';
import { useDesignStore } from '../../store/designStore';
import './Dashboard.css';
export function Dashboard() {
  const navigate = useNavigate();
  const { projects, setProjects, setCurrentProject, setError, error } = useDesignStore();
  const [isLoading, setIsLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      const records = await electronAPI.projects.list();
      setProjects(records);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadProjects();
  }, []);

  const handleCreate = async () => {
    if (!name.trim()) {
      return;
    }
    const project = await electronAPI.projects.create({ name: name.trim() });
    setCurrentProject(project);
    setShowCreate(false);
    setName('');
    await loadProjects();
    navigate(`/projects/${project.id}`);
  };

  const handleDelete = async (projectId: string) => {
    await electronAPI.projects.delete(projectId);
    if (projects.find((project) => project.id === projectId)) {
      await loadProjects();
    }
  };

  return (
    <section className="dashboard-page">
      <div className="dashboard-page__header">
        <div>
          <p className="section-label">Projects</p>
          <h1>Dashboard</h1>
          <p>SQLite に保存されたデザイン変換プロジェクトを管理します。</p>
        </div>
        <div className="dashboard-page__actions">
          <button type="button" onClick={() => navigate('/converter')}>
            クイック変換
          </button>
          <button type="button" onClick={() => setShowCreate(true)}>
            新規プロジェクト
          </button>
        </div>
      </div>

      {error ? <p className="page-error">{error}</p> : null}

      {isLoading ? (
        <div className="dashboard-empty">読み込み中...</div>
      ) : projects.length ? (
        <div className="dashboard-grid">
          {projects.map((project) => (
            <article key={project.id} className="dashboard-card">
              <div>
                <h3>{project.name}</h3>
                <p>{project.image_path ? '画像あり' : '画像未登録'}</p>
                <p className="dashboard-card__meta">{new Date(project.created_at).toLocaleString('ja-JP')}</p>
              </div>
              <div className="dashboard-card__actions">
                <button type="button" onClick={() => navigate(`/projects/${project.id}`)}>
                  開く
                </button>
                <button type="button" className="button--ghost" onClick={() => void handleDelete(project.id)}>
                  削除
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="dashboard-empty">プロジェクトがありません。新規作成またはクイック変換を開始してください。</div>
      )}

      {showCreate ? (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h2>新規プロジェクト</h2>
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Project name" autoFocus />
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
      ) : null}
    </section>
  );
}
