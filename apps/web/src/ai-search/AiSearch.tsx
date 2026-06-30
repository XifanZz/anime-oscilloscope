import { FormEvent, useState } from "react";
import { semanticSearch, type SemanticResponse } from "../api/client";

export function AiSearch() {
  const [query, setQuery] = useState("想看一部中日合拍的悬疑 WEB 连载动画");
  const [response, setResponse] = useState<SemanticResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (query.trim().length < 2) return;
    setLoading(true);
    setError("");
    try {
      setResponse(await semanticSearch(query.trim()));
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="ai-search-section" id="ai-search">
      <div className="section-heading"><div><p className="eyebrow">NATURAL LANGUAGE RETRIEVAL</p><h2>用一句话找番</h2><p>规则先提取年份、地区、类型和标签，再由向量相似度排序；每个结果都解释为什么匹配。</p></div><div className="ai-engine"><span>{response?.engine ?? "等待检索"}</span><small>{response?.model_name ?? "实际引擎会明确显示"}</small></div></div>
      <form className="ai-query" onSubmit={submit}><textarea aria-label="自然语言找番" value={query} onChange={(event) => setQuery(event.target.value)} /><button type="submit" disabled={loading}>{loading ? "正在检索…" : "分析这句话"}</button></form>
      {error && <p className="error-state" role="alert">{error}</p>}
      {response && <><div className="intent-chips"><span>耗时 {response.elapsed_ms.toFixed(1)} ms</span>{response.parsed_intent.year && <span>{response.parsed_intent.year}</span>}{response.parsed_intent.regions.map((region) => <span key={region}>{region}</span>)}{response.parsed_intent.media_types.map((media) => <span key={media}>{media.toUpperCase()}</span>)}{response.parsed_intent.tags.map((tag) => <span key={tag}>#{tag}</span>)}</div><div className="ai-results">{response.results.map((result, index) => <article key={result.anime.id}><div className="ai-rank">{String(index + 1).padStart(2, "0")}</div><div><h3>{result.anime.name_cn ?? result.anime.canonical_name}</h3><p>{result.anime.summary}</p><ul>{result.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul></div><strong>{Math.round(result.confidence * 100)}%<small>匹配置信度</small></strong></article>)}{!response.results.length && <p className="empty-state">没有条目同时满足这些条件，试着减少一个限制。</p>}</div></>}
    </section>
  );
}
