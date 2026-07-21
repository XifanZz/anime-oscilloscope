import { useEffect, useState } from "react";
import {
  MappingCandidatePage,
  getMappingCandidates,
  resolveMappingCandidate,
} from "../api/client";

const reasonLabels: Record<string, string> = {
  media_type_mismatch: "类型不一致",
  air_date_far_apart: "首播日期相距较远",
  episode_count_mismatch: "集数不一致",
  installment_signature_conflict: "季度 / 剧场版 / Part 特征冲突",
};

function percent(value: number | undefined) {
  return `${Math.round((value ?? 0) * 100)}%`;
}

function formatDate(value: string | null) {
  if (!value) return "未知日期";
  return new Date(value).toLocaleDateString("zh-CN");
}

export function MappingReview() {
  const [page, setPage] = useState<MappingCandidatePage | null>(null);
  const [token, setToken] = useState(() => localStorage.getItem("anime-oscilloscope:review-token") ?? "");
  const [message, setMessage] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  const refresh = () => {
    getMappingCandidates()
      .then((response) => setPage(response))
      .catch((error: Error) => setMessage(error.message));
  };

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (token) localStorage.setItem("anime-oscilloscope:review-token", token);
    else localStorage.removeItem("anime-oscilloscope:review-token");
  }, [token]);

  const resolve = async (candidateId: number, decision: "approved" | "rejected") => {
    if (!token.trim()) {
      setMessage("需要管理员复核 token 才能写入数据库；不填写时本页面仅作为公开审阅清单。");
      return;
    }
    setBusyId(candidateId);
    setMessage("");
    try {
      await resolveMappingCandidate(candidateId, decision, token.trim());
      setMessage(decision === "approved" ? "已确认 MAL 映射，下一次采样会写入评分。" : "已拒绝该候选。");
      refresh();
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section className="mapping-review-section" id="mapping-review">
      <div className="section-heading">
        <div>
          <p className="eyebrow">MAL MATCHING / HUMAN REVIEW</p>
          <h2>MAL 人工复核清单</h2>
          <p>自动匹配负责粗筛，疑似续作、Part、剧场版等高风险候选进入这里，由人确认后才写入正式映射。</p>
        </div>
        <label className="review-token">
          管理员 token
          <input
            aria-label="管理员复核 token"
            type="password"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            placeholder="仅站长本地输入"
          />
        </label>
      </div>

      {!page && <div className="empty-state">正在读取 MAL 候选信号…</div>}
      {message && <div className="review-message" role="status">{message}</div>}
      {page && (
        <>
          <div className="review-summary-grid">
            <article><span>待人工复核</span><strong>{page.summary.unresolved_review_count}</strong></article>
            <article><span>已确认映射</span><strong>{page.summary.approved_mapping_count}</strong></article>
            <article><span>仍未映射可排行条目</span><strong>{page.summary.unmapped_rankable_count}</strong></article>
            <article><span>候选队列</span><strong>{page.total}</strong></article>
          </div>
          <div className="review-list">
            {page.items.map((item) => (
              <article className="review-card" key={item.id}>
                <div className="review-title-pair">
                  <div>
                    <span>Bangumi #{item.anime.bangumi_id ?? "—"}</span>
                    <strong>{item.anime.name_cn ?? item.anime.canonical_name}</strong>
                    <small>{item.anime.canonical_name} · {formatDate(item.anime.air_date)} · {item.anime.media_type.toUpperCase()}</small>
                  </div>
                  <div>
                    <span>MAL #{item.external_id}</span>
                    <a href={item.external_url} target="_blank" rel="noreferrer">{item.title}</a>
                    <small>生成于 {formatDate(item.generated_at)}</small>
                  </div>
                </div>
                <div className="review-evidence">
                  <span>置信度 <b>{percent(item.confidence)}</b></span>
                  <span>标题 <b>{percent(item.evidence.title_similarity)}</b></span>
                  <span>日期 <b>{percent(item.evidence.date_similarity)}</b></span>
                  <span>类型 <b>{percent(item.evidence.media_similarity)}</b></span>
                  <span>集数 <b>{percent(item.evidence.episode_similarity)}</b></span>
                </div>
                <div className="review-reasons">
                  {(item.evidence.reasons?.length ? item.evidence.reasons : ["需要人工确认"]).map((reason) => (
                    <span key={reason}>{reasonLabels[reason] ?? reason}</span>
                  ))}
                  {item.evidence.installment_conflict && <span>检测到系列特征冲突</span>}
                </div>
                <div className="review-actions">
                  <button type="button" disabled={busyId === item.id} onClick={() => resolve(item.id, "approved")}>确认映射</button>
                  <button type="button" disabled={busyId === item.id} onClick={() => resolve(item.id, "rejected")}>拒绝候选</button>
                </div>
              </article>
            ))}
            {!page.items.length && <div className="empty-state">当前没有待复核 MAL 候选。可以运行批量匹配工作流生成新候选。</div>}
          </div>
        </>
      )}
    </section>
  );
}

