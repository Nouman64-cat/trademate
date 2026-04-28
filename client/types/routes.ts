export interface CostBreakdown {
  inland_haulage:        number;
  origin_thc:            number;
  ocean_air_freight_min: number;
  ocean_air_freight_max: number;
  transshipment_thc:     number;
  fixed_charges:         number;
  destination_thc:       number;
  customs_broker:        number;
  drayage:               number;
  hmf:                   number;
  mpf:                   number;
  import_duty:           number;
  total_min:             number;
  total_max:             number;
}

export interface TransitBreakdown {
  inland_days:       number;
  sea_air_days_min:  number;
  sea_air_days_max:  number;
  port_processing:   number;
  customs_days:      number;
  total_min:         number;
  total_max:         number;
}

export interface RouteAlert {
  level:   "info" | "warning" | "critical";
  message: string;
}

export interface RouteResult {
  id:                  string;
  name:                string;
  mode:                "SEA" | "AIR";
  origin_port:         string;
  hubs:                string[];
  destination_ports:   string[];
  carriers:            string[];
  frequency_per_week:  number;
  reliability_score:   number;
  cost:                CostBreakdown;
  transit:             TransitBreakdown;
  score:               number;
  tag:                 "cheapest" | "fastest" | "balanced" | null;
  alerts:              RouteAlert[];
  rate_source:         "live" | "static";
}

// Trade direction. PK_TO_US = Pakistan → USA, US_TO_PK = USA → Pakistan.
export type RouteDirection = "PK_TO_US" | "US_TO_PK";

export interface RouteEvaluationResponse {
  direction:        RouteDirection;
  origin_city:      string;
  destination_city: string;
  cargo_type:       string;
  cargo_value_usd:  number;
  hs_code:          string | null;
  duty_rate_pct:    number;
  cost_weight:      number;
  routes:           RouteResult[];
  recommended:      { cheapest: string; fastest: string; balanced: string };
  disclaimer:       string;
}

export interface RouteOptions {
  direction:          RouteDirection;
  origin_cities:      string[];
  destination_cities: string[];
  cargo_types: { value: string; label: string }[];
}

export interface RouteEvaluationRequest {
  direction?:        RouteDirection;
  origin_city:       string;
  destination_city:  string;
  cargo_type:        string;
  cargo_value_usd:   number;
  hs_code?:          string;
  cargo_volume_cbm?: number;
  cargo_weight_kg?:  number;
  cargo_length_cm?:  number;
  cargo_width_cm?:   number;
  cargo_height_cm?:  number;
  cost_weight:       number;
}
