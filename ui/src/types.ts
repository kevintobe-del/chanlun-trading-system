export type Timeframe = "1d" | "60m" | "30m" | "5m";

export interface Bar {
  id: string;
  index: number;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
}

export interface StructureUnit {
  id: string;
  direction: "up" | "down";
  start_index: number;
  end_index: number;
  start_price: number;
  end_price: number;
  raw_start: number;
  raw_end: number;
  confirmed_at: string;
  available_at: string;
  definition_mode?: string;
  method?: string;
  stroke_ids?: string[];
  approximation_loss?: string[];
  power: Record<string, number | null>;
}

export interface Fractal {
  id: string;
  kind: "top" | "bottom";
  raw_index: number;
  price: number;
  confirmed_at: string;
  available_at: string;
}

export interface Center {
  id: string;
  unit_type: "stroke" | "segment_proxy";
  component_ids: string[];
  zd: number;
  zg: number;
  gg: number;
  dd: number;
  raw_start: number;
  raw_end: number;
  confirmed_at: string;
  available_at: string;
  definition_mode: string;
  approximation_loss: string[];
}

export interface Divergence {
  id: string;
  direction: "bullish" | "bearish";
  unit_type: string;
  compared_ids: string[];
  new_extreme: boolean;
  baseline: {
    method: string;
    previous: number;
    current: number;
    weaker: boolean | null;
    supports_candidate: boolean;
  };
  u1: {
    method: string;
    role: string;
    votes: Record<string, boolean | null>;
    weaker_votes: number;
    available_votes: number;
    supports_candidate: boolean;
  };
  decision: "candidate" | "not_present" | "insufficient_evidence";
  confirmed_at: string;
  available_at: string;
  invalidation: string;
}

export interface Analysis {
  meta: {
    schema_version: string;
    engine_version: string;
    symbol: string;
    timeframe: Timeframe;
    generated_at: string;
    as_of: string;
    source: string;
    input_sha256: string;
    definition_mode: string;
    execution_allowed: false;
  };
  quality: {
    status: "pass" | "warn" | "fail";
    row_count: number;
    volume_coverage: number;
    warnings: string[];
  };
  bars: Bar[];
  indicators: {
    macd: {dif: number[]; dea: number[]; hist: number[]};
  };
  layers: {
    merged_bars: Array<Record<string, unknown>>;
    fractals: Fractal[];
    strokes: StructureUnit[];
    segments: StructureUnit[];
    centers: Center[];
    divergences: Divergence[];
  };
  state: {
    structure: string;
    current_center_id: string | null;
    candidate_signals: Array<{
      id: string;
      label: string;
      kind: string;
      at_index: number;
      price: number;
      evidence_ids: string[];
      status: string;
      action: "NO_ACTION";
    }>;
    invalidation: string[];
    execution_allowed: false;
  };
}

export interface AnalysisBundle {
  symbol: string;
  name?: string;
  source: string;
  is_synthetic: boolean;
  frames: Partial<Record<Timeframe, Analysis>>;
  failures?: Partial<Record<Timeframe, string>>;
}

export interface ReportLevel {
  timeframe: "1w" | "1d" | "30m" | "5m";
  status: string;
  bars: number;
  asof?: string;
  pos_vs_last_zs?: "above_zs" | "in_zs" | "below_zs" | null;
}

export interface MultilevelReport {
  id: string;
  symbol: string;
  name: string;
  status: "buy_candidate" | "sell_risk" | "observe" | string;
  report_text: string;
  created_at: string;
  source: {provider: string; name: string};
  result: {
    contract: string;
    meta: {
      asof: string | null;
      definition_mode?: string;
      trade_level: string;
      confirm_level: string;
      trigger_level: string;
      ai_tokens: number;
    };
    levels: Record<"1w" | "1d" | "30m" | "5m", ReportLevel & Record<string, unknown>>;
    verdict: {
      action: string;
      verdict: string;
      confirmation_30m: boolean;
      trigger_5m: boolean;
      invalidations: Array<{invalidation: {rule: string; px: number}}>;
      next_observation: string[];
      definition_mode: string;
      execution_allowed: false;
    };
    caveats: string[];
    data_refresh?: {timeframes: Record<string, {fetched?: number; error?: string}>};
  };
}

export interface ReportSettings {
  analysis: {daily_years: number; minute30_years: number; minute5_days: number};
  webhooks: {
    feishu_enabled: boolean;
    feishu_configured: boolean;
    feishu_secret_configured: boolean;
    wecom_enabled: boolean;
    wecom_configured: boolean;
  };
  automation: {
    automatic_enabled: boolean;
    premarket_time: string;
    after_close_time: string;
    default_send_report: boolean;
  };
  shared_source: {id: string; provider: string; name: string};
}

export interface LayerVisibility {
  fractals: boolean;
  strokes: boolean;
  segments: boolean;
  centers: boolean;
  divergence: boolean;
  signals: boolean;
  volume: boolean;
  macd: boolean;
}

export interface DataSourceItem {
  id: string;
  provider: "yfinance" | "tushare" | "akshare";
  name: string;
  builtin: boolean;
  has_api_key: boolean;
  api_key_mask: string;
  active: boolean;
}

export interface DataSourceConfig {
  active_id: string;
  sources: DataSourceItem[];
  providers: Record<string, {label: string; requires_key: boolean}>;
}

export interface WatchlistItem {
  symbol: string;
  name: string;
  last_searched_at?: string;
}

export interface WatchlistPool {
  id: string;
  name: string;
  builtin: boolean;
  items: WatchlistItem[];
}

export interface WatchlistConfig {
  history: WatchlistItem[];
  pools: WatchlistPool[];
}
