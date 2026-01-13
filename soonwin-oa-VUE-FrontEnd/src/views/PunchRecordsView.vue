<template>
  <div class="punch-records-container">
    <el-page-header content="打卡记录" @back="goBack">
      <template #extra>
        <el-button @click="logout">退出登录</el-button>
      </template>
    </el-page-header>
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
        </el-form-item>
      </el-form>

      <!-- 打卡记录表格 -->
      <el-table
        :data="punchRecords"
        v-loading="loading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{background: '#f5f7fa', color: '#606266'}"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="emp_id" label="员工工号" width="120" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="punch_type" label="打卡类型" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.punch_type === '上班打卡' ? 'success' : 'warning'">
              {{ scope.row.punch_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="punch_time" label="打卡时间" width="180" />
        <el-table-column prop="inner_ip" label="打卡IP" width="150" />
        <el-table-column prop="phone_mac" label="设备MAC" width="180" />
        <el-table-column prop="last_login_time" label="最后登录时间" width="180">
          <template #default="scope">
            {{ scope.row.last_login_time ? new Date(scope.row.last_login_time).toLocaleString('zh-CN') : '无记录' }}
          </template>
        </el-table-column>
        <el-table-column prop="login_device" label="登录设备" width="180" />
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import request from '@/utils/request';
import { PunchRecord } from '@/types';

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

// 返回上一页
const goBack = () => {
  router.go(-1);
};

// 退出登录
const logout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '确认退出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    // 清除本地存储的token
    localStorage.removeItem('oa_token');
    // 提示用户
    ElMessage.success('已退出登录');
    // 跳转到登录页
    router.push('/login');
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel') {
      console.error('退出登录失败：', error);
    }
  }
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
</style>