<template>
  <div class="punch-records-container">
    <CommonHeader title="打卡记录" />
    <el-divider></el-divider>

    <el-card shadow="hover" class="records-card">
      <!-- 搜索筛选区域 -->
      <el-form :model="searchForm" :inline="true" class="search-form">
        <el-form-item label="员工姓名">
          <el-input v-model="searchForm.name" placeholder="请输入员工姓名" clearable></el-input>
        </el-form-item>
        <el-form-item label="员工工号">
          <el-input v-model="searchForm.empId" placeholder="请输入员工工号" clearable></el-input>
        </el-form-item>
        <el-form-item label="打卡类型">
          <el-select v-model="searchForm.punchType" placeholder="请选择打卡类型" clearable>
            <el-option label="上班打卡" value="上班打卡"></el-option>
            <el-option label="下班打卡" value="下班打卡"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="打卡时间">
          <el-date-picker
            v-model="searchForm.punchTimeRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          ></el-date-picker>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchPunchRecords">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
          <el-button type="success" @click="refreshData">刷新</el-button>
          <el-button type="warning" @click="exportToXlsx">导出XLSX</el-button>
        </el-form-item>
      </el-form>

      <!-- 打卡记录表格 -->
      <el-table
        :data="punchRecords"
        v-loading="loading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{background: '#f5f7fa', color: '#606266', 'text-align': 'center'}"
        :cell-style="{'text-align': 'center', 'vertical-align': 'middle'}"
      >
        <el-table-column prop="emp_id" label="工号" width="120" align="center" header-align="center" />
        <el-table-column prop="name" label="姓名" width="120" align="center" header-align="center" />
        <el-table-column prop="punch_type" label="打卡类型" width="120" align="center" header-align="center">
          <template #default="scope">
            <el-tag :type="scope.row.punch_type === '上班打卡' ? 'success' : 'warning'">
              {{ scope.row.punch_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="打卡时间" width="150" align="center" header-align="center">
          <template #default="scope">
            <div>{{ scope.row.punch_time ? formatDateToYMD(new Date(scope.row.punch_time)) : '' }}</div>
            <div>{{ scope.row.punch_time ? new Date(scope.row.punch_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : '' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="最后登录时间" width="180" align="center" header-align="center">
          <template #default="scope">
            <div>{{ scope.row.last_login_time ? formatDateToYMD(new Date(scope.row.last_login_time)) : '无记录' }}</div>
            <div>{{ scope.row.last_login_time ? new Date(scope.row.last_login_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : '' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="login_device" label="设备" width="150" align="center" header-align="center" />
        <el-table-column label="操作" width="150" fixed="right" align="center" header-align="center">
          <template #default="scope">
            <el-button type="primary" size="small" @click="showDetails(scope.row)">详情</el-button>
            <el-button type="danger" size="small" @click="deleteRecord(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页组件 -->
      <el-pagination
        v-model="pagination.page"
        :page-size="pagination.size"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        class="pagination"
      />
    </el-card>
    
    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="打卡记录详情"
      width="600px"
      :before-close="closeDetailDialog"
    >
      <el-descriptions v-if="selectedRecord" :column="1" border>
        <el-descriptions-item label="ID">{{ selectedRecord.id }}</el-descriptions-item>
        <el-descriptions-item label="工号">{{ selectedRecord.emp_id }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ selectedRecord.name }}</el-descriptions-item>
        <el-descriptions-item label="打卡类型">
          <el-tag :type="selectedRecord.punch_type === '上班打卡' ? 'success' : 'warning'">
            {{ selectedRecord.punch_type }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="打卡时间">
          <div v-if="selectedRecord.punch_time">
            <div>{{ formatDateToYMD(new Date(selectedRecord.punch_time)) }}</div>
            <div>{{ new Date(selectedRecord.punch_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}</div>
          </div>
          <div v-else>无记录</div>
        </el-descriptions-item>
        <el-descriptions-item label="打卡IP">{{ selectedRecord.inner_ip }}</el-descriptions-item>
        <el-descriptions-item label="设备ID">{{ selectedRecord.device_id }}</el-descriptions-item>
        <el-descriptions-item label="最后登录时间">
          <div v-if="selectedRecord.last_login_time">
            <div>{{ formatDateToYMD(new Date(selectedRecord.last_login_time)) }}</div>
            <div>{{ new Date(selectedRecord.last_login_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}</div>
          </div>
          <div v-else>无记录</div>
        </el-descriptions-item>
        <el-descriptions-item label="登录设备">{{ selectedRecord.login_device }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeDetailDialog">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import * as XLSX from 'xlsx';
import request from '@/utils/request';
import { PunchRecord } from '@/types';
import { getOperations } from '@/api/attendance';
import { AttendanceOperation } from '@/types/attendance';
import CommonHeader from '@/components/CommonHeader.vue';

// 路由实例
const router = useRouter();

// 分页参数
const pagination = ref({
  page: 1,
  size: 10,
  total: 0
});

// 搜索表单
const searchForm = ref({
  name: '',
  empId: '',
  punchType: '',
  punchTimeRange: [] as string[],
});

// 打卡记录数据
const punchRecords = ref<PunchRecord[]>([]);
const loading = ref(false);

// 详情弹窗相关
const detailDialogVisible = ref(false);
const selectedRecord = ref<PunchRecord | null>(null);

// 获取打卡记录
const fetchPunchRecords = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.value.page,
      size: pagination.value.size,
      name: searchForm.value.name || undefined,
      emp_id: searchForm.value.empId || undefined,
      punch_type: searchForm.value.punchType || undefined,
      start_date: searchForm.value.punchTimeRange?.[0] || undefined,
      end_date: searchForm.value.punchTimeRange?.[1] || undefined,
    };

    const response = await request.get('/api/punch-records', { params });
    // 现在API返回格式统一：{code: 200, msg: "...", data: {list: [...], total: x, page: x, size: x}}
    // request拦截器会返回data部分，即{list: [...], total: x, page: x, size: x}
    punchRecords.value = response.list || [];  // 打卡记录数组
    pagination.value.total = response.total || 0;
    pagination.value.page = response.page || 1;
    pagination.value.size = response.size || 10;
  } catch (error) {
    console.error('Error fetching punch records:', error);
    ElMessage.error('获取打卡记录失败');
  } finally {
    loading.value = false;
  }
};

// 重置搜索
const resetSearch = () => {
  searchForm.value = {
    name: '',
    empId: '',
    punchType: '',
    punchTimeRange: [],
  };
  pagination.value.page = 1;
  fetchPunchRecords();
};

// 刷新数据
const refreshData = () => {
  fetchPunchRecords();
};

// 日期格式化函数，格式为 YYYYMMDD
const formatDate = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}${month}${day}`;
};

// 日期格式化函数，格式为 YYYY-MM-DD
const formatDateToYMD = (date: Date): string => {
  if (!date || isNaN(date.getTime())) return '';
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

// 处理分页大小改变
const handleSizeChange = (newSize: number) => {
  pagination.value.size = newSize;
  pagination.value.page = 1;
  fetchPunchRecords();
};

// 处理当前页改变
const handleCurrentChange = (newPage: number) => {
  // 当使用v-model时，不需要手动更新pagination.value.page，因为v-model会自动更新
  // 但为了明确起见，我们仍然可以设置它
  pagination.value.page = newPage;
  fetchPunchRecords();
};

// 组件挂载时获取数据
onMounted(() => {
  fetchPunchRecords();
});

// 显示详情
const showDetails = (record: PunchRecord) => {
  selectedRecord.value = record;
  detailDialogVisible.value = true;
};

// 删除打卡记录
const deleteRecord = async (record: PunchRecord) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除员工 ${record.name}(${record.emp_id}) 在 ${record.punch_time} 的打卡记录吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    // 调用后端删除API
    await request.delete(`/api/punch-records/${record.id}`);
    
    ElMessage.success('打卡记录删除成功');
    // 刷新列表
    fetchPunchRecords();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除打卡记录失败');
    }
  }
};

// 关闭详情弹窗
const closeDetailDialog = () => {
  detailDialogVisible.value = false;
  selectedRecord.value = null;
};


// 导出打卡与考勤记录到 XLSX
// 打卡区：按"员工 × 当前日期范围"展开完整矩阵，缺卡日保留行（时间留空）
// 考勤区：单 sheet 内隔一行，列出每位命中员工在日期范围内的考勤操作
const exportToXlsx = async () => {
  try {
    ElMessage.info('正在导出数据，请稍候...');

    // 1. 拉所有命中筛选的打卡记录（不分页）
    const params = {
      page: 1,
      size: 999999,
      name: searchForm.value.name || undefined,
      emp_id: searchForm.value.empId || undefined,
      punch_type: searchForm.value.punchType || undefined,
      start_date: searchForm.value.punchTimeRange?.[0] || undefined,
      end_date: searchForm.value.punchTimeRange?.[1] || undefined,
    };

    const punchResp = await request.get('/api/punch-records', { params });
    const allRecords: PunchRecord[] = punchResp.list || [];

    if (allRecords.length === 0) {
      ElMessage.warning('没有可导出的打卡数据');
      return;
    }

    // 2. 按员工（用工号做 key）+ 日期聚合
    const recordMap = new Map<string, Map<string, { 上班: PunchRecord[]; 下班: PunchRecord[] }>>();
    // 记录员工信息（用工号索引，避免姓名变化导致重复员工）
    const empInfoMap = new Map<string, { emp_id: string; name: string }>();

    allRecords.forEach(record => {
      const empKey = record.emp_id;
      empInfoMap.set(empKey, { emp_id: record.emp_id, name: record.name });
      const dateStr = formatDateToYMD(new Date(record.punch_time));

      if (!recordMap.has(empKey)) {
        recordMap.set(empKey, new Map());
      }
      const dateMap = recordMap.get(empKey)!;
      if (!dateMap.has(dateStr)) {
        dateMap.set(dateStr, { 上班: [], 下班: [] });
      }
      const typeRecords = dateMap.get(dateStr)!;
      if (record.punch_type === '上班打卡') {
        typeRecords.上班.push(record);
      } else if (record.punch_type === '下班打卡') {
        typeRecords.下班.push(record);
      }
    });

    // 3. 计算日期范围数组
    // 优先用用户选的日期范围；没选则用数据中实际存在的日期范围
    let dateList: string[] = [];
    if (searchForm.value.punchTimeRange?.[0] && searchForm.value.punchTimeRange?.[1]) {
      dateList = getDateRangeList(
        searchForm.value.punchTimeRange[0],
        searchForm.value.punchTimeRange[1]
      );
    } else {
      const dateSet = new Set<string>();
      recordMap.forEach(dateMap => {
        dateMap.forEach((_, d) => dateSet.add(d));
      });
      dateList = Array.from(dateSet).sort();
    }

    // 4. 构建 AOA（打卡区）
    const aoa: any[][] = [];
    aoa.push(['工号', '姓名', '日期', '上班打卡时间', '下班打卡时间']);

    const sortedEmpKeys = Array.from(recordMap.keys()).sort();

    sortedEmpKeys.forEach(empKey => {
      const emp = empInfoMap.get(empKey)!;
      const dateMap = recordMap.get(empKey)!;

      dateList.forEach(dateStr => {
        const typeRecords = dateMap.get(dateStr);

        let punchInTime = '';
        let punchOutTime = '';
        if (typeRecords) {
          if (typeRecords.上班.length > 0) {
            const earliest = typeRecords.上班.reduce((min, record) =>
              new Date(record.punch_time) < new Date(min.punch_time) ? record : min
            );
            punchInTime = new Date(earliest.punch_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
          }
          if (typeRecords.下班.length > 0) {
            const latest = typeRecords.下班.reduce((max, record) =>
              new Date(record.punch_time) > new Date(max.punch_time) ? record : max
            );
            punchOutTime = new Date(latest.punch_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
          }
        }

        aoa.push([emp.emp_id, emp.name, dateStr, punchInTime, punchOutTime]);
      });
    });

    // 5. 拉命中员工在日期范围内的考勤操作
    const attendanceOps: AttendanceOperation[] = [];
    const startTime = searchForm.value.punchTimeRange?.[0]
      ? `${searchForm.value.punchTimeRange[0]} 00:00:00` : undefined;
    const endTime = searchForm.value.punchTimeRange?.[1]
      ? `${searchForm.value.punchTimeRange[1]} 23:59:59` : undefined;

    // 后端 get_operations 一次只支持单个 emp_id，逐位员工拉取
    for (const empId of sortedEmpKeys) {
      try {
        const ops = await getOperations({
          emp_id: empId,
          start_time: startTime,
          end_time: endTime,
        });
        if (Array.isArray(ops)) {
          attendanceOps.push(...ops);
        }
      } catch (err) {
        console.warn(`拉取员工 ${empId} 考勤记录失败`, err);
      }
    }

    // 6. 空一行 → 考勤表头 → 考勤记录
    aoa.push([]);
    aoa.push(['工号', '姓名', '操作类型', '开始时间', '结束时间', '时长(小时)', '事由', '状态', '申请时间']);

    attendanceOps
      .sort((a, b) => {
        if (a.emp_id !== b.emp_id) return a.emp_id.localeCompare(b.emp_id);
        return (a.start_time || '').localeCompare(b.start_time || '');
      })
      .forEach(op => {
        aoa.push([
          op.emp_id,
          op.name,
          OPERATION_TYPE_LABELS[op.operation_type] || op.operation_type,
          op.start_time || '',
          op.end_time || '',
          op.duration ?? '',
          op.reason || '',
          OPERATION_STATUS_LABELS[op.operation_status] || op.operation_status,
          op.create_time || '',
        ]);
      });

    // 7. 生成 XLSX
    const ws = XLSX.utils.aoa_to_sheet(aoa);
    // 设置列宽
    ws['!cols'] = [
      { wch: 12 }, // 工号
      { wch: 12 }, // 姓名
      { wch: 18 }, // 日期 / 开始时间
      { wch: 18 }, // 上班打卡时间 / 结束时间
      { wch: 18 }, // 下班打卡时间 / 时长
      { wch: 30 }, // 事由
      { wch: 12 }, // 状态
      { wch: 18 }, // 申请时间
      { wch: 10 },
    ];
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '打卡与考勤');

    XLSX.writeFile(wb, `打卡考勤_${formatDate(new Date())}.xlsx`);

    // 统计打卡行数：第三列存在且是日期串的行（排除空行与考勤表头）
    const punchRowCount = aoa.filter(r => r[0] && r[2] && r.length >= 3).length - 1; // 减去表头
    ElMessage.success(`导出成功：打卡 ${punchRowCount} 行，考勤 ${attendanceOps.length} 条`);
  } catch (error) {
    console.error('Export error:', error);
    ElMessage.error('导出失败');
  }
};

// 生成 [start, end] 区间内所有日期字符串（YYYY-MM-DD，含首尾）
const getDateRangeList = (startDate: string, endDate: string): string[] => {
  const result: string[] = [];
  const start = new Date(startDate);
  const end = new Date(endDate);
  const cur = new Date(start);
  while (cur <= end) {
    result.push(formatDateToYMD(cur));
    cur.setDate(cur.getDate() + 1);
  }
  return result;
};

// 考勤操作类型 / 状态中文标签
const OPERATION_TYPE_LABELS: Record<string, string> = {
  leave: '请假',
  overtime: '加班',
  make_up: '补卡',
  appeal: '申诉',
  business_trip: '出差',
  adjust: '调整',
};

const OPERATION_STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  submitted: '待审批',
  approving: '审批中',
  approved: '已批准',
  rejected: '已驳回',
  cancelled: '已撤销',
};

</script>

<style scoped>
.punch-records-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.records-card {
  margin-top: 20px;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.dialog-footer {
  text-align: right;
}
</style>