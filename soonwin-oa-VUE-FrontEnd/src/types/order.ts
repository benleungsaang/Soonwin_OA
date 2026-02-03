// types/order.ts
export interface OrderBasicInfo {
  id: number;
  contract_no: string;
  order_no: string;
  machine_no: string;
  machine_name: string;
  machine_model: string;
  machine_count: number;
  order_time: string | null;
  ship_time: string | null;
  current_status: string;
}

// types/progress.ts
export interface StatusDetail {
  id: string;
  status: string;
  start_time: string | null;
  expected_complete_time: string | null;
  actual_complete_time: string | null;
}

export interface ProgressMedia {
  id: string;
  file_type: string;
  file_url: string;
  file_name: string;
  upload_time: string;
}

export interface ProgressItem {
  id: string;
  title: string;
  status: '未完成' | '已完成';
  remark: string;
  create_time: string;
  update_time: string | null;
  media_files: ProgressMedia[];
}

export interface ProgressStat {
  completed: number;
  total: number;
  rate: number;
}

export interface OrderProgressDetail {
  order_info: OrderBasicInfo;
  progress_info: {
    current_status: string;
    status_details: StatusDetail[];
  };
  progress_items: ProgressItem[];
  progress_stat: ProgressStat;
}