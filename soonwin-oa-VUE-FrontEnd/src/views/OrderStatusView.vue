<template>
  <div class="order-status-container">
    <!-- 公共头部 -->
    <CommonHeader title="订单进度" />

    <!-- 订单列表区域 -->
    <div class="order-list-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>待处理订单列表</span>
          </div>
        </template>

        <!-- 订单表格 -->
        <el-table
          :data="orders"
          style="width: 100%"
          @row-click="showOrderDetails"
          v-loading="loading"
        >
          <el-table-column prop="contract_no" label="合同编号" width="150" />
          <el-table-column prop="machine_name" label="名称" width="150" />
          <el-table-column prop="machine_model" label="机型" width="120" />
          <el-table-column prop="order_time" label="下单时间" width="120">
            <template #default="scope">
              {{ formatDate(scope.row.order_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="ship_time" label="出货时间" width="120">
            <template #default="scope">
              {{ formatDate(scope.row.ship_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="creator_id" label="订单负责人" width="120" />
          <el-table-column label="任务完成进度" width="150">
            <template #default="scope">
              <div
                style="cursor: pointer; display: flex; flex-direction: column; align-items: center;"
                @click.stop="showOrderDetails(scope.row)"
              >
                <div style="width: 100px; height: 8px; background: rgba(255, 186, 98, 0.6); border-radius: 4px; overflow: hidden;">
                  <div
                    :style="{width: `${getOrderStatusProgress(scope.row.id)}%`, height: '100%'}"
                    style="background: #67c23a; border-radius: 4px;"
                  ></div>
                </div>
                <div class="progress-text" style="margin-top: 2px;">
                  {{ getOrderStatusFraction(scope.row.id) }}
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="250" fixed="right">
            <template #default="scope">
              <div style="display: flex; gap: 5px; justify-content: center;">
                <template v-if="scope.row.status_id">
                  <!-- 如果订单已有状态记录，显示简报、详细和删除按钮 -->
                  <el-button
                    type="primary"
                    size="small"
                    @click.stop="goToReport(scope.row)"
                  >
                    <el-icon class="opera-btn" style="margin-right: 5px;"><List /></el-icon> 简报
                  </el-button>
                  <el-button
                    v-if="isSalesOrAdmin"
                    type="info"
                    size="small"
                    @click.stop="goToDetailedReport(scope.row)"
                  >
                    <el-icon class="opera-btn" style="margin-right: 5px;"><Document /></el-icon> 复盘
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    @click.stop="deleteOrderStatus(scope.row.id, scope.row.status_id)"
                  >
                    <el-icon class="opera-btn" style="margin-right: 5px;"><Delete /></el-icon> 删除
                  </el-button>
                </template>
                <template v-else>
                  <!-- 如果订单没有状态记录，显示创建按钮 -->
                  <el-button
                    type="success"
                    size="small"
                    @click.stop="createOrderStatus(scope.row.id)"
                  >
                    <el-icon style="margin-right: 5px;"><Plus /></el-icon> 创建
                  </el-button>
                </template>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页组件 -->
        <el-pagination
          class="pagination"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
        />
      </el-card>
    </div>

    <!-- 订单进度详情弹窗 -->
    <el-dialog
      v-model="orderDetailDialogVisible"
      :title="`订单进度详情 - ${selectedOrderDetail?.contract_no || selectedOrder?.contract_no || ''}`"
      :width="isMobile ? '95%' : '80%'"
      :before-close="handleCloseOrderDetailDialog"
    >
      <div v-if="selectedOrderDetail || selectedOrder">
        <!-- 订单基础信息卡片 -->
        <el-card class="order-info-card">
          <template #header>
            <div class="card-header">
              <span>订单基础数据</span>
            </div>
          </template>
          <div class="order-info-container">
            <el-descriptions :column="isMobile ? 1 : 2" border>
              <el-descriptions-item label="合同编号">{{ (selectedOrderDetail || selectedOrder).contract_no }}</el-descriptions-item>
              <el-descriptions-item label="订单编号">{{ (selectedOrderDetail || selectedOrder).order_no }}</el-descriptions-item>
              <el-descriptions-item label="包装机单号">{{ (selectedOrderDetail || selectedOrder).machine_no }}</el-descriptions-item>
              <el-descriptions-item label="名称">{{ (selectedOrderDetail || selectedOrder).machine_name }}</el-descriptions-item>
              <el-descriptions-item label="机型">{{ (selectedOrderDetail || selectedOrder).machine_model }}</el-descriptions-item>
              <el-descriptions-item label="主机数量">{{ (selectedOrderDetail || selectedOrder).machine_count }}</el-descriptions-item>
              <el-descriptions-item label="下单时间">{{ formatDate((selectedOrderDetail || selectedOrder).order_time) }}</el-descriptions-item>
              <el-descriptions-item label="出货时间">{{ formatDate((selectedOrderDetail || selectedOrder).ship_time) }}</el-descriptions-item>
            </el-descriptions>

            <el-descriptions title="当前进度" border>
              <el-descriptions-item label="总进度">
                <div class="progress-container">
                  <div style="width: 100%; height: 8px; background: rgba(255, 186, 98, 0.6); border-radius: 4px; overflow: hidden;">
                    <div :style="{width: (selectedOrderDetail && selectedOrderDetail.completed_tasks !== undefined ? getOrderProgress(selectedOrderDetail.completed_tasks, selectedOrderDetail.total_tasks) : 0) + '%', height: '100%'}" style="background: #67c23a; border-radius: 4px;"></div>
                  </div>
                  <div class="progress-text" style="margin-top: 2px;">
                    {{ (selectedOrderDetail && selectedOrderDetail.completed_tasks !== undefined) ? selectedOrderDetail.completed_tasks : 0 }} / {{ (selectedOrderDetail && selectedOrderDetail.total_tasks !== undefined) ? selectedOrderDetail.total_tasks : 0 }}
                  </div>
                </div>
              </el-descriptions-item>
              <el-descriptions-item :span="1" label="添加进度">
              <el-tooltip content="快速创建进度" placement="bottom">
                <el-icon class="btn-add-status" style="background-color: #67c23a;margin-right: 5px;" @click="openAddStatusLogDialog"><Plus /></el-icon>
              </el-tooltip>
              <el-tooltip content="批量导入状态" placement="bottom">
                <el-icon class="btn-add-status" style="background-color: #629cd9;margin-right: 5px;" @click="openBatchStatusDialog"><DocumentCopy /></el-icon>
              </el-tooltip>
              <el-tooltip v-if="showClearStatusBtn" content="清空状态" placement="bottom">
                <el-icon class="btn-add-status" style="background-color: #d9b062;" @click="clearAllStatusData"><Refresh /></el-icon>
              </el-tooltip>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>

        <!-- 订单状态日志卡片 -->
        <el-card body-style="padding:8px;" v-for="(statusLog, logIndex) in statusLogs" :key="statusLog.id" class="status-log-card">
          <template #header>
            <div class="card-header status-header" >

              <div style="display: flex;gap: 20px;">
                  <span class="clickable-field card-title" @click.stop="openEditFieldDialog(statusLog, 'status', '修改状态', updateStatusLogStatus)">{{ statusLog.status }}</span>
                <div class="progress-container">
                  <div style="width: 100px; height: 8px; background: rgba(255, 186, 98, 0.6); border-radius: 4px; overflow: hidden;">
                    <div :style="{width: getStatusLogProgress(statusLog.id) + '%', height: '100%'}" style="background: #67c23a; border-radius: 4px;"></div>
                  </div>
                  <div class="progress-text" style="margin-top: 2px;">
                    {{ getStatusLogCompletionInfo(statusLog.id) }}
                  </div>
                </div>
              </div>

              <div>
                <el-icon class="btn-add-task" @click.stop="addStatusTask(statusLog.id)"><Plus /></el-icon>
                <el-icon class="btn-del-status" @click.stop="deleteStatusLog(statusLog.id)"><Delete /></el-icon>
                <el-icon @click.stop="toggleStatusLog(statusLog.id)" :class="['expand-icon', {'expanded': expandedStatusLogs[statusLog.id] === true}]"><ArrowRight /></el-icon>
              </div>

            </div>
          </template>
          <div class="order-info-container" v-show="expandedStatusLogs[statusLog.id] === true">
            <el-descriptions  class="sub-card"
              v-for="(statusTask, taskIndex) in getStatusLogTasks(statusLog.id)"
              :key="statusTask.id"
              direction="vertical"
              :column="3"
              border
            >
            <el-descriptions-item :span="3" label="照片">
              <div class="upload-container">
                <el-tooltip content="可直接拖入图片或视频" placement="bottom">
                    <ImageUploadPreview
                      :ref="setUploadPreviewRef(statusTask)"
                      :task-id="getValidTaskId(statusTask)"
                      @upload-success="onMediaUploadSuccess"
                      @upload-failure="onMediaUploadFailure"
                      @upload-clipboard-image="onUploadClipboardMedia"
                    />
                  </el-tooltip>
                  <el-tooltip content="点击输入框后按CTRL+V，可以粘贴剪切的图片" placement="bottom">
                    <el-input
                      style="margin: 5px;width:100%;"
                      @paste="(e) => handleInputPaste(e, getValidTaskId(statusTask))"
                      placeholder="粘贴图片(Ctrl+V)"
                    ></el-input>
                  </el-tooltip>
                </div>

                <div class="task-img-container"> <!-- 原有上传组件不变 -->
                  <!-- 修改：使用解析后的媒体文件数组渲染，包含图片和视频缩略图 -->
                  <template v-if="getTaskMediaFiles(statusTask).length">
                    <div
                      v-for="(media, mediaIndex) in getTaskMediaFiles(statusTask)"
                      :key="`media-${statusTask.id}-${mediaIndex}`"
                      class="thumb-wrapper"
                    >
                      <!-- 内层容器：裁剪图片内容 -->
                      <div class="thumb-inner-container">
                        <!-- 图片文件显示 -->
                        <el-image
                          v-if="media.file_type === 'image'"
                          :src="media.thumb || media.url"
                          :preview-src-list="getTaskMediaUrls(statusTask)"
                          :initial-index="mediaIndex"
                          preview-teleported
                          close-on-press-esc
                          hide-on-click-modal
                          class="thumb-img"
                        />
                        <!-- 视频文件显示 -->
                        <div
                          v-else-if="media.file_type === 'video'"
                          class="video-container"
                        >
                          <!-- 视频缩略图作为封面，与图片缩略图保持一致的样式 -->
                          <img
                            v-if="media.thumb"
                            :src="media.thumb"
                            class="thumb-img video-thumb"
                            style="cursor: pointer;"
                            @click="$event.stopPropagation(); playVideo(media.url)"
                          />
                          <!-- 如果没有缩略图，显示默认背景和图标 -->
                          <div
                            v-else
                            class="thumb-img video-thumb"
                            style="background-color: #f0f0f0; display: flex; align-items: center; justify-content: center; cursor: pointer;"
                            @click="playVideo(media.url)"
                          >
                            <el-icon style="font-size: 20px; color: #999;"><VideoCamera /></el-icon>
                          </div>
                        </div>
                      </div>
                      <!-- 删除按钮：定位到外层容器，不会被裁剪 -->
                      <el-button
                        class="delete-img-btn"
                        size="small"
                        @click="deleteMediaFromTemplate(statusTask, Number(mediaIndex))"
                      >
                        <el-icon><Close /></el-icon>
                      </el-button>
                      <!-- 文件类型指示器：定位到外层容器，不会被裁剪 -->
                      <div v-if="media.file_type === 'video'" class="file-type-indicator">
                        <el-icon><VideoCamera /></el-icon>
                      </div>
                      <!-- 播放按钮覆盖层：仅对视频显示 -->
                      <div v-if="media.file_type === 'video'" class="video-play-overlay" @click.stop="playVideo(media.url)">
                        <el-icon style="color: white; font-size: 16px;"><VideoPlay /></el-icon>
                      </div>
                    </div>
                  </template>


                </div>
              </el-descriptions-item>

              <el-descriptions-item :span="1" width="150px" label="项目名" >
                <span class="clickable-field" @click.stop="openEditFieldDialog(statusTask, 'name', '修改任务名称', updateStatusTask)">{{ statusTask.name || '点击添加标题' }}</span>
              </el-descriptions-item>
              <el-descriptions-item :span="1" label="备注信息" >
                <span class="clickable-field" @click.stop="openEditFieldDialog(statusTask, 'description', '修改任务描述', updateStatusTask)">{{ statusTask.description || '点击添加描述' }}</span>
              </el-descriptions-item>
              <el-descriptions-item :span="1" width="250px" label="操作" >
                 <el-switch
                  v-model="statusTask.is_completed"
                  size="large"
                  active-text="完成"
                  inactive-text="未完成"
                  @change="updateStatusTask(statusTask)"
                />
                <el-icon class="btn-del-task" @click="deleteTask(statusTask.task_id)"><Delete /></el-icon>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>

        <!-- 底部操作区域 -->
        <div class="bottom-actions">
          <div class="progress-summary">
            <p>任务项进度：</p>
          </div>
          <div class="action-buttons">
            <el-button  @click="handleCloseOrderDetailDialog">
              关闭
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 添加订单状态日志模态框 -->
    <el-dialog
      v-model="showAddStatusLogDialog"
      title="添加订单状态日志"
      width="400px"
    >
      <el-form :model="newStatusLogForm" label-width="120px">
        <el-form-item label="状态" required>
          <el-input v-model="newStatusLogForm.status" placeholder="请输入状态名称" />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="newStatusLogForm.start_time"
            type="datetime"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="预计完成时间">
          <el-date-picker
            v-model="newStatusLogForm.expected_completion_time"
            type="datetime"
            placeholder="选择预计完成时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddStatusLogDialog = false">取消</el-button>
          <el-button type="primary" @click="addStatusLog">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 添加任务模态框 -->
    <el-dialog
      v-model="showAddTaskDialog"
      title="添加任务"
      width="400px"
    >
      <el-form :model="newTaskForm" label-width="120px">
        <el-form-item label="任务名称" required>
          <el-input v-model="newTaskForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input
            v-model="newTaskForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入任务描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddTaskDialog = false">取消</el-button>
          <el-button type="primary" @click="addTask">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 通用修改字段模态框 -->
    <el-dialog
      v-model="editFieldDialog.visible"
      :title="editFieldDialog.title"
      width="400px"
    >
      <el-input
        v-model="editFieldDialog.value"
        :type="'textarea'"
        :rows="4"
        :placeholder="`请输入${editFieldDialog.title}`"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editFieldDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="saveFieldEdit">确定</el-button>
        </span>
      </template>
    </el-dialog>



    <!-- 批量创建状态日志对话框 -->
    <el-dialog
      v-model="showBatchStatusDialog"
      title="批量创建状态日志"
      width="800px"
      :before-close="() => { showBatchStatusDialog = false; }"
      class="mobile-dialog"
    >
      <div>
        <p>请输入状态和任务数据，格式如下：</p>
        <!-- 根据返回类型显示图片或文本 -->
        <div v-if="isStatusImageFormat">
          <img :src="statusFormatDescription" alt="匹配格式示例" style="max-width: 100%; height: auto; border: 1px solid #e6e6e6; border-radius: 4px;">
        </div>
        <pre v-else style="background-color: #f5f5f5; padding: 10px; border-radius: 4px; margin: 10px 0; white-space: pre-wrap; word-break: break-all;">
{{ statusFormatDescription }}
        </pre>

        <el-input
          v-model="batchStatusInputText"
          :rows="10"
          type="textarea"
          placeholder="请按上述格式输入数据，例如：\n下单	发单，排产\n排产	采购，生产，回厂前确认"
        />

        <!-- 匹配结果展示 -->
        <div v-if="isStatusMatched" class="match-results-section" style="margin-top: 20px;">
          <h4>匹配结果：</h4>

          <!-- 已匹配状态 -->
          <div v-if="matchedStatuses.length > 0" class="matched-statuses-section">
            <h5 style="color: #67c23a;">已匹配状态 ({{ matchedStatuses.length }}个)：</h5>
            <el-table :data="matchedStatuses" style="width: 100%; margin-top: 8px;">
              <el-table-column prop="status" label="状态" width="150"></el-table-column>
              <el-table-column prop="tasks" label="任务项" show-overflow-tooltip>
                <template #default="scope">
                  <div>
                    <el-tag
                      v-for="(task, index) in scope.row.tasks"
                      :key="index"
                      size="small"
                      style="margin-right: 5px; margin-bottom: 5px; display: inline-block;"
                    >
                      {{ task }}
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 未匹配数据 -->
          <div v-if="unmatchedStatuses.length > 0" class="unmatched-statuses-section" style="margin-top: 15px;">
            <h5 style="color: #e6a23c;">未匹配数据 ({{ unmatchedStatuses.length }}个)：</h5>
            <div style="background: #fdf6ec; border: 1px solid #faecd8; border-radius: 4px; padding: 10px; margin-top: 8px;">
              <span v-for="(item, index) in unmatchedStatuses" :key="index" class="unmatched-item">
                {{ item }}{{ index < unmatchedStatuses.length - 1 ? ', ' : '' }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showBatchStatusDialog = false">取消</el-button>
          <el-button
            type="warning"
            @click="matchBatchStatusData"
          >
            匹配数据
          </el-button>
          <el-button
            :disabled="!isStatusMatched"
            type="primary"
            @click="batchCreateStatusLogs"
          >
            批量创建
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 全局视频播放模态框 -->
    <div v-if="showVideoPlayer" class="video-modal-overlay" @click="closeVideoPlayer">
      <div class="video-modal-content" @click.stop>
        <video
          ref="videoRef"
          :src="currentVideoSrc"
          controls
          autoplay
          class="video-player"
          @click.stop
          @error="onVideoError"
        ></video>
        <div class="video-controls">
          <button class="close-btn" @click="closeVideoPlayer">关闭</button>
        </div>
      </div>
    </div>

  </div>



</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import request from '@/utils/request';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, List, Document, DocumentCopy, Close, Delete, ArrowRight, Refresh, Film, VideoPlay, VideoCamera } from '@element-plus/icons-vue';

import CommonHeader from '@/components/CommonHeader.vue';
import ImageUploadPreview from '@/components/ImageUploadPreview.vue';
import { cursorTo } from 'node:readline';
import { parseJsonToFiles, getJsonFormatDescription } from '@/utils/excel-parse';
import { hasModulePermission, ModuleNames, getCurrentUserRole } from '@/utils/authUtils';

// 获取路由实例
const router = useRouter();

// ===================== 响应式数据 =====================
const orders = ref<any[]>([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const orderDetailDialogVisible = ref(false);
const selectedOrder = ref<any>({});
const selectedOrderDetail = ref<any>(null);
const selectedStatus = ref<any>(null);
const tasks = ref<any[]>([]);
const uploadPreviewRefs = ref<{[key: number]: any}>({}); // 存储ImageUploadPreview组件引用
const windowWidth = ref(window.innerWidth);
const is_completed = ref(false); // 补充缺失的响应式变量

// 视频播放相关
const showVideoPlayer = ref(false);
const currentVideoSrc = ref('');
const videoRef = ref<HTMLVideoElement | null>(null);

// 订单状态日志相关
const showAddStatusLogDialog = ref(false);
const newStatusLogForm = ref({
  status: '',
  start_time: '',
  expected_completion_time: ''
});
const currentOrderStatusId = ref(null);
const statusLogs = ref<any[]>([]);

// 图片上传预览相关
const showImageUploadPreview = ref(false);
const currentImageUploadTaskId = ref<number | null>(null);

// 任务相关
const newTaskForm = ref({
  name: '',
  description: '',
  category: '',
  status_log_id: null
});
const currentTaskStatusLogId = ref(null);
const showAddTaskDialog = ref(false);

// 用于跟踪状态日志的展开/折叠状态
const expandedStatusLogs = ref<{[key: number]: boolean}>({});



// 批量创建状态日志相关
const showBatchStatusDialog = ref(false); // 批量创建状态日志对话框显示状态
const batchStatusInputText = ref(''); // 批量状态输入文本
const matchedStatuses = ref<any[]>([]); // 匹配的状态数据
const unmatchedStatuses = ref<string[]>([]); // 未匹配的状态数据
const isStatusMatched = ref(false); // 状态是否已匹配


// ===================== 图片数据结构化处理 =====================
/**
 * 将任务的媒体文件解析为结构化数组（仅支持新数据格式）
 * @param task 任务对象
 * @returns 媒体文件对象数组 [{ url: '', thumb: '', file_type: '' }, ...]
 */
const getTaskMediaFiles = (task: any) => {
  if (!task) return [];

  // 仅使用新的media_files字段
  if (task.media_files && Array.isArray(task.media_files)) {
    return task.media_files
      .filter((file: any) => file.file_type === 'image' || file.file_type === 'video') // 获取图片和视频
      .map((file: any) => ({
        url: file.file_path,
        thumb: file.thumb_path || file.file_path, // 如果没有缩略图，使用原图
        id: file.id,  // 媒体文件ID，用于删除操作
        file_type: file.file_type  // 文件类型：image或video
      }));
  }

  // 如果没有新格式数据，返回空数组
  return [];
};

/**
 * 将任务的图片路径字符串解析为结构化数组（仅支持新数据格式）
 * @param task 任务对象
 * @returns 图片对象数组 [{ url: '', thumb: '' }, ...]
 */
const getTaskImages = (task: any) => {
  if (!task) return [];

  // 仅使用新的media_files字段
  if (task.media_files && Array.isArray(task.media_files)) {
    return task.media_files
      .filter((file: any) => file.file_type === 'image') // 只获取图片
      .map((file: any) => ({
        url: file.file_path,
        thumb: file.thumb_path || file.file_path, // 如果没有缩略图，使用原图
        id: file.id  // 媒体文件ID，用于删除操作
      }));
  }

  // 如果没有新格式数据，返回空数组
  return [];
};

/**
 * 获取任务的媒体文件URL列表（用于预览）
 * @param task 任务对象
 * @returns 媒体文件URL数组
 */
const getTaskMediaUrls = (task: any) => {
  return getTaskMediaFiles(task).map(media => media.url); // 总是返回原图用于预览
};

/**
 * 获取任务的图片URL列表（用于预览）
 * @param task 任务对象
 * @returns 图片URL数组
 */
const getTaskImageUrls = (task: any) => {
  return getTaskImages(task).map(img => img.url);
};



/**
 * 安全获取任务ID
 * @param task 任务对象
 * @returns 有效的任务ID或undefined
 */
const getValidTaskId = (task: any) => {
  const id = task?.task_id || task?.id;
  return id ? Number(id) : undefined;
};

// ===================== 计算属性 =====================
// 判断是否为移动端
const isMobile = computed(() => windowWidth.value < 768);

// 计算属性：状态格式说明
const statusFormatDescription = computed(() => {
  return getJsonFormatDescription('status');
});

// 判断是否为图片格式
const isStatusImageFormat = computed(() => {
  const desc = statusFormatDescription.value;
  return desc.endsWith('.png') || desc.endsWith('.jpg') || desc.endsWith('.jpeg') || desc.endsWith('.gif') || desc.endsWith('.webp');
});

// 控制清空状态按钮的显示：非管理员用户显示此按钮
const showClearStatusBtn = computed(() => {
  const userRole = getCurrentUserRole();
  return userRole !== 'admin';
});

// 计算属性：判断当前用户是否为sales或admin
const isSalesOrAdmin = computed(() => {
  const userRole = getCurrentUserRole();
  return userRole === 'sales' || userRole === 'admin';
});

// 获取用户角色
const userRole = ref('');

// 切换状态日志的展开/折叠状态
const toggleStatusLog = (statusLogId: number) => {
  const currentState = expandedStatusLogs.value[statusLogId];
  expandedStatusLogs.value[statusLogId] = !(currentState === true);
};


const getOrderProgress = (completed_tasks:number, total_tasks:number) => {
  const completed = completed_tasks || 0;
  const total = total_tasks || 0;

  // 计算百分比，避免除零错误
  if (total === 0) {
    return 0;
  }

  return Math.round((completed / total) * 100);
};

// 计算每个状态日志的进度
const getStatusLogProgress = (statusLogId: number) => {
  const tasks = getStatusLogTasks(statusLogId);
  if (tasks.length === 0) return 0;

  const completedTasks = tasks.filter((task: any) => task.is_completed).length;
  return Math.round((completedTasks / tasks.length) * 100);
};

// 获取某个状态日志的任务项
const getStatusLogTasks = (statusLogId: number) => {
  const tasks_list = tasks.value.filter((task: any) => task.status_log_id === statusLogId)
  return tasks_list;
};

// 获取状态日志的完成信息
const getStatusLogCompletionInfo = (statusLogId: number) => {
  const tasks = getStatusLogTasks(statusLogId);
  const completedTasks = tasks.filter((task: any) => task.is_completed).length;
  return `${completedTasks} / ${tasks.length}`;
};

// 实时计算进度
const realTimeProgress = computed(() => {
  // 统计所有子任务（sub tasks）
  const allSubTasks = tasks.value.filter((task: any) => task.item_type === 'sub' && !task._toBeDeleted);
  const totalTasks = allSubTasks.length;

  // 统计已完成的子任务
  const completedTasks = allSubTasks.filter((task: any) => task.is_completed).length;

  // 计算进度百分比
  const progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  return {
    total_tasks: totalTasks,
    completed_tasks: completedTasks,
    progress: progress
  };
});

// ===================== 表单校验规则 =====================


// ===================== 工具方法 =====================
// 通用修改字段相关
const editFieldDialog = ref({
  visible: false,
  title: '',
  value: '',
  object: null,
  field: '',
  updateCallback: null
});

// 通用修改字段函数
const openEditFieldDialog = (obj: any, field: string, title: string, updateCallback?: any) => {
  editFieldDialog.value = {
    visible: true,
    title: title,
    value: obj[field] || '',
    object: obj,
    field: field,
    updateCallback: updateCallback
  };
};

// 更新状态日志状态
const updateStatusLogStatus = async (statusLog: any, field: string, newValue: string) => {
  try {
    const payload: any = {};
    payload[field] = newValue;

    const response: any = await request.put(`/api/order-status-logs/${statusLog.id}`, payload);

    if (response && response.code === 200) {
      ElMessage.success('状态日志更新成功');
    }
  } catch (error) {
    console.error('更新状态日志失败:', error);
    ElMessage.error('更新状态日志失败');
    // 如果API调用失败，回滚本地更改
    statusLog[field] = editFieldDialog.value.value; // 原来的值
  }
};

// 保存修改的字段
const saveFieldEdit = async () => {
  if (!editFieldDialog.value.object || !editFieldDialog.value.field) {
    ElMessage.error('缺少对象或字段信息');
    return;
  }

  const obj = editFieldDialog.value.object;
  const field = editFieldDialog.value.field;
  const newValue = editFieldDialog.value.value;
  const updateCallback = editFieldDialog.value.updateCallback;

  // 更新对象的字段值
  obj[field] = newValue;

  // 如果有自定义回调函数，则执行它
  if (updateCallback && typeof updateCallback === 'function') {
    await updateCallback(obj, field, newValue);
  }

  // 关闭对话框
  editFieldDialog.value.visible = false;
  ElMessage.success(`${editFieldDialog.value.title}修改成功`);
};

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toISOString().split('T')[0];
};

// 监听窗口大小变化
const handleResize = () => {
  windowWidth.value = window.innerWidth;
};

// ===================== 业务逻辑方法 =====================
// 显示订单详情
const showOrderDetails = async (row: any) => {
  selectedOrderDetail.value = { ...row };
  orderDetailDialogVisible.value = true;

  // 加载订单状态详情
  await loadOrderStatusDetails();
};

// 简报类型选择对话框相关
const showReportTypeDialog = ref(false);
const selectedRow = ref<any>(null);
const reportType = ref('basic'); // 'basic' 或 'with-inquiry'

// 跳转到订单进度报告页面（一般简报）
const goToReport = (row: any) => {
  // 检查是否有订单状态ID
  if (row.status_id) {
    // 在新标签页中打开报告页面
    const url = `/order-status-report?orderId=${row.status_id}`;
    window.open(url, '_blank');
  } else {
    ElMessage.warning('该订单尚无状态记录，无法生成报告');
  }
};
// 生成订单进度报告（带询盘详情）
const generateReportWithInquiry = async () => {
  if (!selectedRow.value || !selectedRow.value.id) {
    ElMessage.warning('订单信息不完整');
    return;
  }

  try {
    // 首先获取订单详情以获取关联的询盘ID
    const orderDetailsResponse: any = await request.get(`/api/orders/${selectedRow.value.id}`);
    const orderDetails = orderDetailsResponse;

    if (!orderDetails || !orderDetails.inquiry_id) {
      ElMessage.warning('该订单未关联询盘，无法生成带询盘详情的简报');
      // 如果没有关联询盘，仍然可以生成一般简报
      const url = `/order-status-report?orderId=${selectedRow.value.status_id}`;
      window.open(url, '_blank');
      showReportTypeDialog.value = false;
      return;
    }

    // 获取询盘详情
    const inquiryResponse: any = await request.get(`/api/inquiries/${orderDetails.inquiry_id}`);
    const inquiryDetails = inquiryResponse;

    // 在URL中添加询盘详情参数
    const url = `/order-status-report?orderId=${selectedRow.value.status_id}&withInquiry=true&inquiryId=${orderDetails.inquiry_id}`;
    window.open(url, '_blank');

    showReportTypeDialog.value = false;
  } catch (error) {
    console.error('获取询盘详情失败:', error);
    ElMessage.error('获取询盘详情失败，将生成一般简报');

    // 失败时仍然生成一般简报
    const url = `/order-status-report?orderId=${selectedRow.value.status_id}`;
    window.open(url, '_blank');
    showReportTypeDialog.value = false;
  }
};

// 生成一般简报
const generateBasicReport = () => {
  if (selectedRow.value && selectedRow.value.status_id) {
    const url = `/order-status-report?orderId=${selectedRow.value.status_id}`;
    window.open(url, '_blank');
    showReportTypeDialog.value = false;
  } else {
    ElMessage.warning('订单信息不完整');
  }
};

// 确认简报类型选择
// const confirmReportType = () => {
//   if (reportType.value === 'with-inquiry') {
//     generateReportWithInquiry();
//   } else {
//     generateBasicReport();
//   }
// };

// 关闭订单详情对话框
const handleCloseOrderDetailDialog = () => {
  orderDetailDialogVisible.value = false;
  selectedOrderDetail.value = null;
  selectedStatus.value = null;
  tasks.value = [];
};

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true;
  try {
    const response: any = await request.get('/api/order-status-orders', {
      params: {
        page: currentPage.value,
        size: pageSize.value
      }
    });

    // 处理返回的订单数据，确保有status_id字段
    const processedOrders = (response.list || []).map((order: any) => {
      // 如果后端返回status_id字段，直接使用；否则设置为null
      return {
        ...order,
        status_id: order.status_id || null
      };
    });

    orders.value = processedOrders;
    total.value = response.total || 0;
  } catch (error) {
    console.error('获取订单列表失败:', error);
    ElMessage.error('获取订单列表失败');
  } finally {
    loading.value = false;
  }
};

// 获取订单进度百分比
const getOrderStatusProgress = (orderId: number) => {
  const order = orders.value.find((o: any) => o.id === orderId);
  return order ? (order.progress_percent || 0) : 0;
};

// 获取订单进度的分数格式 (如: "1/3")
const getOrderStatusFraction = (orderId: number) => {
  const order = orders.value.find((o: any) => o.id === orderId);
  if (!order) return '0/0';

  const completedTasks = order.completed_tasks || 0;
  const totalTasks = order.total_tasks || 0;

  return `${completedTasks}/${totalTasks}`;
};

// 分页 - 每页条数变化
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  fetchOrders();
};

// 分页 - 当前页变化
const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  fetchOrders();
};

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const tokenStr = localStorage.getItem('oa_token');
    if (tokenStr) {
      const tokenParts = tokenStr.split('.');
      if (tokenParts.length === 3) {
        try {
          const payload = JSON.parse(atob(tokenParts[1]));
          userRole.value = payload.user_role || 'user';
        } catch (e) {
          console.error('解析token失败:', e);
          userRole.value = 'user';
        }
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error);
    userRole.value = 'user';
  }
};

// 关闭视频播放器
const closeVideoPlayer = () => {
  showVideoPlayer.value = false;
  if (videoRef.value) {
    videoRef.value.pause();
  }
};

// 视频错误处理
const onVideoError = (event: Event) => {
  ElMessage.error('视频加载失败');
};

// ESC键关闭视频播放器
const handleEscKey = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && showVideoPlayer.value) {
    closeVideoPlayer();
  }
};

// 监听键盘事件
onMounted(() => {
  document.addEventListener('keydown', handleEscKey);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscKey);
});

// ===================== 业务逻辑方法 =====================

// 打开添加状态日志对话框
const openAddStatusLogDialog = () => {
  if (!selectedOrderDetail.value && !selectedOrder.value) {
    ElMessage.error('请先选择一个订单');
    return;
  }

  // 如果还没有创建订单状态记录，先创建一个
  if (!selectedOrderDetail.value.status_id) {
    ElMessage.error('此订单尚无状态记录，请先创建');
    return;
  }

  currentOrderStatusId.value = selectedOrderDetail.value.status_id;
  showAddStatusLogDialog.value = true;
  // 重置表单
  newStatusLogForm.value = {
    status: '',
    start_time: '',
    expected_completion_time: ''
  };
};

// 添加状态日志
const addStatusLog = async () => {
  if (!newStatusLogForm.value.status) {
    ElMessage.error('请输入状态名称');
    return;
  }

  try {
    const response: any = await request.post('/api/order-status-logs', {
      order_status_id: currentOrderStatusId.value,
      status: newStatusLogForm.value.status,
      start_time: newStatusLogForm.value.start_time,
      expected_completion_time: newStatusLogForm.value.expected_completion_time
    });

    if (response) {
      ElMessage.success('状态日志添加成功');
      statusLogs.value.push(response);
      showAddStatusLogDialog.value = false;

      // 重新加载订单状态详情
      await loadOrderStatusDetails();
    }
  } catch (error) {
    console.error('添加状态日志失败:', error);
    ElMessage.error('添加状态日志失败');
  }
};

// 打开批量创建状态日志对话框
const openBatchStatusDialog = () => {
  if (!selectedOrderDetail.value && !selectedOrder.value) {
    ElMessage.error('请先选择一个订单');
    return;
  }

  // 如果还没有创建订单状态记录，先创建一个
  if (!selectedOrderDetail.value.status_id) {
    ElMessage.error('此订单尚无状态记录，请先创建');
    return;
  }

  currentOrderStatusId.value = selectedOrderDetail.value.status_id;
  showBatchStatusDialog.value = true;
  // 重置表单
  batchStatusInputText.value = '';
  matchedStatuses.value = [];
  unmatchedStatuses.value = [];
  isStatusMatched.value = false;
};

// 批量匹配状态数据
const matchBatchStatusData = () => {
  try {
    // 解析输入文本
    const inputText = batchStatusInputText.value.trim();
    if (!inputText) {
      ElMessage.error('请输入匹配信息');
      return;
    }

    // 第一步：将所有连续空白（制表符、多个空格、全角空格）统一替换为单个制表符
    const normalizedText = inputText.replace(/[\s\u00A0]+/g, '\t');
    // 第二步：按换行符分割行（兼容\r\n和\n）
    let lines = normalizedText.split(/\r?\n/).filter(line => line.trim() !== '');

    // 核心修复：处理无换行符的场景（所有内容在一行）
    if (lines.length === 1) {
      const allFields = lines[0].split('\t').map(field => field.trim()).filter(field => field);
      // 检查是否是表头+多行数据混在一起的情况（表头2个字段，总字段数>=2且能被2整除）
      if (allFields.length >= 2 && allFields.slice(0, 2).join(',') === '状态,进度项') {
        // 分离表头和数据
        const headerFields = allFields.slice(0, 2); // 前2个是表头
        const dataFields = allFields.slice(2);     // 后面的是数据

        // 按每2个字段为一行拆分数据
        const newLines = [headerFields.join('\t')]; // 重新构建表头行
        for (let i = 0; i < dataFields.length; i += 2) {
          const rowFields = dataFields.slice(i, i+2);
          if (rowFields.length >= 1) { // 至少有状态字段
            newLines.push(rowFields.join('\t'));
          }
        }
        lines = newLines; // 使用重构后的行数据
      }
    }

    if (lines.length === 0) {
      ElMessage.error('请输入匹配信息');
      return;
    }

    // 解析表头
    const headers = lines[0].split('\t').map(header => header.trim());

    // 校验表头（增加容错性，处理大小写和空白问题）
    if (headers.length < 2 ||
        headers[0].toLowerCase().trim() !== '状态' ||
        headers[1].toLowerCase().trim() !== '进度项') {
      ElMessage.error('表头格式不正确，请使用：状态\t进度项');
      return;
    }

    // 解析数据行
    const dataRows = lines.slice(1).map(line => {
      const fields = line.split('\t').map(field => field.trim());
      // 确保至少有状态字段，进度项字段可选（补空）
      if (fields.length >= 1 && fields[0]) {
        return {
          status: fields[0] || '',
          progressItems: fields[1] || ''
        };
      }
      return null;
    }).filter(row => row !== null);

    // 处理结果 - 将匹配的数据转换为状态和任务格式
    const matchedStatusesTemp = [];
    const unmatchedStatusesTemp = [];

    dataRows.forEach((data: any) => {
      if (data.status && data.progressItems) {
        // 解析进度项为任务数组
        const tasks = data.progressItems.split('，').map(task => task.trim()).filter(task => task);
        matchedStatusesTemp.push({
          status: data.status,
          tasks: tasks
        });
      } else if (data.status) {
        // 只有状态没有进度项
        matchedStatusesTemp.push({
          status: data.status,
          tasks: []
        });
      } else {
        // 使用data对象的字符串表示作为未匹配项
        const dataStr = Object.values(data || {}).join(',');
        unmatchedStatusesTemp.push(dataStr || '未知数据');
      }
    });

    // 更新匹配结果
    matchedStatuses.value = matchedStatusesTemp;
    unmatchedStatuses.value = unmatchedStatusesTemp;
    isStatusMatched.value = matchedStatusesTemp.length > 0;

    // 提示信息
    if (unmatchedStatusesTemp.length > 0) {
      ElMessage.warning(`以下行未找到匹配格式: ${unmatchedStatusesTemp.join(', ')}`);
    }

    if (matchedStatusesTemp.length === 0) {
      ElMessage.warning('没有找到匹配的数据');
      isStatusMatched.value = false;
    } else {
      ElMessage.success(`匹配成功: ${matchedStatusesTemp.length} 个状态已匹配`);
    }
  } catch (error: any) {
    console.error('匹配状态数据失败:', error);
    ElMessage.error(error.message || '解析状态数据失败，请检查格式');
    isStatusMatched.value = false;
  }
};

// 批量创建状态日志和任务
const batchCreateStatusLogs = async () => {
  if (matchedStatuses.value.length === 0) {
    ElMessage.warning('没有匹配的状态数据可创建');
    return;
  }

  try {
    // 构建要发送的数据
    const batchData = {
      order_status_id: currentOrderStatusId.value,
      statuses: matchedStatuses.value
    };


    // 使用新的批量创建API
    // 注意：由于request.ts会自动解包data，这里response已经是后端返回的data部分
    const response: any = await request.post('/api/order-status-logs/batch', batchData);


    // 成功：后端返回的data部分包含创建结果
    ElMessage.success(`批量创建完成: ${response.created_status_logs.length} 个状态日志, ${response.created_tasks.length} 个任务`);
    showBatchStatusDialog.value = false;

    // 重新加载订单状态详情
    await loadOrderStatusDetails();
  } catch (error: any) {
    console.error('批量创建状态日志失败:', error);

    // 根据错误类型提供更具体的错误消息
    if (error.response) {
      // 服务器返回了错误状态码
      console.error('HTTP错误:', error.response.status, error.response.data);
      ElMessage.error(`批量创建失败: ${error.response.data.msg || `HTTP ${error.response.status}`}`);
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('网络错误:', error.request);
      ElMessage.error('网络错误，请检查后端服务是否正常运行');
    } else {
      // 其他错误
      console.error('请求错误:', error.message);
      ElMessage.error(`批量创建失败: ${error.message || '未知错误'}`);
    }
  }
};
// 添加状态任务
const addStatusTask = async (statusLogId: number) => {
  // 从statusLogs中查找对应的状态日志，获取其status作为category
  const statusLog = statusLogs.value.find((log: any) => log.id === statusLogId);
  const category = statusLog ? statusLog.status : '默认分类';

  // 设置新任务表单的初始值
  newTaskForm.value = {
    name: '新任务',
    description: '请输入任务描述',
    category: category,
    status_log_id: statusLogId
  };

  // 显示添加任务模态框
  showAddTaskDialog.value = true;
  currentTaskStatusLogId.value = statusLogId;
};

// 添加任务
const addTask = async () => {
  if (!newTaskForm.value.name || newTaskForm.value.name.trim() === '') {
    ElMessage.warning('任务名称不能为空');
    return;
  }

  try {
    const response: any = await request.post('/api/order-status/' + currentOrderStatusId.value + '/tasks', {
      status_log_id: currentTaskStatusLogId.value,
      name: newTaskForm.value.name.trim(),
      category: newTaskForm.value.category,
      description: newTaskForm.value.description
    });

    if (response) {
      ElMessage.success('任务添加成功');
      // 从response.data中获取完整的任务信息（因为API返回格式为{code, data, msg}，request.ts会自动解包data部分）
      // 根据API响应格式，response应该是包含任务详细信息的对象
      const taskResponse = response; // request.ts已解包data部分

      // 构建任务项，确保包含所有必需的字段
      const taskItem = {
        id: taskResponse.id || taskResponse.task_id,                      // 使用返回的ID作为id
        task_id: taskResponse.id || taskResponse.task_id,                 // 使用返回的ID作为task_id
        name: taskResponse.name || newTaskForm.value.name,
        category: taskResponse.category || newTaskForm.value.category,
        description: taskResponse.description || newTaskForm.value.description,
        is_completed: taskResponse.is_completed || false,
        photo_path: taskResponse.photo_path || '',
        thumb_photo_path: taskResponse.thumb_photo_path || '',
        status_log_id: taskResponse.status_log_id || currentTaskStatusLogId.value,
        create_time: taskResponse.create_time,
        update_time: taskResponse.update_time,
        sort_order: taskResponse.sort || taskResponse.sort_order || 0,    // 兼容不同的排序字段名
        parent_id: taskResponse.status_log_id || currentTaskStatusLogId.value, // 兼容不同的父级字段名
        item_type: 'sub',                                                 // 固定为sub类型
        // 添加新的媒体文件字段
        media_files: taskResponse.media_files || [],
        images: taskResponse.images || [],
        videos: taskResponse.videos || [],
        image_count: taskResponse.image_count || 0,
        video_count: taskResponse.video_count || 0
      };

      tasks.value.push(taskItem);

      // 关闭模态框并重置表单
      showAddTaskDialog.value = false;
      newTaskForm.value = {
        name: '',
        description: '',
        category: '',
        status_log_id: null
      };

      // 重新加载订单状态详情，以确保所有数据同步
      await loadOrderStatusDetails();
    }
  } catch (error) {
    console.error('添加任务失败:', error);
    ElMessage.error('添加任务失败');
  }
};

// 更新状态任务
const updateStatusTask = async (task: any) => {
  try {
    const response: any = await request.put(`/api/order-status/${currentOrderStatusId.value}/tasks/${task.id || task.task_id}`, {
      is_completed: task.is_completed,
      name: task.name,
      description: task.description
    });
    if (response) {
      // 找到对应的任务并更新其数据
      const taskIndex = tasks.value.findIndex((t: any) => t.id === (task.id || task.task_id));
      if (taskIndex > -1) {
        // 将服务器返回的任务对象转换为前端期望的结构
        const taskItem = {
          task_id: response.task_id,
          id: response.task_id,
          name: response.name,
          category: response.category,
          description: response.description,
          is_completed: response.is_completed,
          photo_path: response.photo_path,
          thumb_photo_path: response.thumb_photo_path,
          status_log_id: response.status_log_id,
          create_time: response.create_time,
          update_time: response.update_time,
          sort_order: response.sort,
          parent_id: response.status_log_id,
          item_type: 'sub'
        };
        tasks.value[taskIndex] = taskItem;
      }
      ElMessage.success('任务更新成功');

      // 重新加载订单状态详情以更新进度信息
      await loadOrderStatusDetails();

      // 重新获取订单列表以更新待处理订单列表中的进度信息
      await fetchOrders();
    }

  } catch (error) {
    console.error('更新任务失败:', error);
    ElMessage.error('更新任务失败');
  }

};



// 删除状态日志
const deleteStatusLog = async (statusLogId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此状态日志吗？删除后将无法恢复，相关的任务也会被删除。', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    const response: any = await request.delete(`/api/order-status-logs/${statusLogId}`);

    // request.ts会自动解包data，对于DELETE请求，如果成功但data为undefined，
    // 拦截器会返回undefined，所以我们需要特殊处理这种情况
    // 检查请求是否成功完成（没有抛出异常）
    ElMessage.success('状态日志删除成功');
    // 从本地数据中移除该状态日志
    statusLogs.value = statusLogs.value.filter((log: any) => log.id !== statusLogId);
    // 同时移除与该状态日志关联的任务
    tasks.value = tasks.value.filter((task: any) => task.status_log_id !== statusLogId);
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除状态日志失败:', error);
      ElMessage.error('删除状态日志失败');
    }
  }
};

// ===================== 修改删除图片函数（核心修复） =====================
const deleteImage = async (task: any, imgIndex: number, taskId?: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这张图片吗？删除后将无法恢复。', '确认删除', {
      type: 'warning'
    });

    // 1. 解析当前图片为结构化数组
    const currentImages = getTaskImages(task);

    // 2. 边界校验
    if (imgIndex < 0 || imgIndex >= currentImages.length) {
      ElMessage.error('图片索引超出范围');
      return;
    }

    // 3. 获取要删除的图片信息
    const imageToDelete = currentImages[imgIndex];
    const actualTaskId = taskId || (task.task_id ? Number(task.task_id) : undefined) || (task.id ? Number(task.id) : undefined);

    // 验证任务ID是否有效
    if (!actualTaskId) {
      ElMessage.error('无法删除图片：任务ID无效');
      return;
    }

    // 4. 优先使用新的媒体文件ID进行删除
    let response;
      response = await request.delete(`/api/order-status/${currentOrderStatusId.value}/tasks/${actualTaskId}/media`, {
        data: { media_file_id: imageToDelete.id }
      });

    if (response) {
      // 5. 更新本地任务数据
      const taskIndex = tasks.value.findIndex(t =>
        Number(t.task_id || t.id || 0) === Number(actualTaskId || 0)
      );
      if (taskIndex > -1) {
        const newTasks = [...tasks.value];

        if (imageToDelete.id) {
          // 从media_files数组中移除对应的媒体文件
          const updatedMediaFiles = newTasks[taskIndex].media_files?.filter((file: any) => file.id !== imageToDelete.id) || [];
          newTasks[taskIndex] = {
            ...newTasks[taskIndex],
            media_files: updatedMediaFiles,
            images: updatedMediaFiles.filter((file: any) => file.file_type === 'image'),
            image_count: updatedMediaFiles.filter((file: any) => file.file_type === 'image').length
          };
        }
        // 不再处理旧格式数据，因为现在全部使用media_files格式

        tasks.value = newTasks;
      }
    }

    ElMessage.success('图片删除成功');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除图片失败:', error);
      ElMessage.error('删除图片失败');
    }
  }
};

// 创建订单状态记录
const createOrderStatus = async (orderId: number) => {
  try {
    await ElMessageBox.confirm('确定要为该订单创建状态记录吗？', '确认创建', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    // POST请求会返回完整的响应，request.ts会自动解包data部分
    const response: any = await request.post('/api/order-status', {
      order_id: orderId
    });

    // 由于request.ts自动解包，response直接就是后端返回的data部分
    // response现在直接包含订单状态记录的数据，而不是{code, data, msg}格式
    // 后端返回格式: {code: 200, msg: "...", data: {...status_record_data...}}
    // 经过request.ts解包后，response直接是status_record_data或成功消息
    ElMessage.success('订单状态记录创建成功');

    // 重新加载订单列表以更新状态
    await fetchOrders();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('创建订单状态记录失败:', error);
      // 检查错误是否包含响应信息
      if (error.response && error.response.data && error.response.data.msg) {
        ElMessage.error(error.response.data.msg);
      } else {
        ElMessage.error('创建订单状态记录失败');
      }
    }
  }
};

// 删除订单状态记录
const deleteOrderStatus = async (orderId: number, statusId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除该订单的状态记录吗？删除后将无法恢复！', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    // DELETE请求可能返回undefined或简单的成功消息，而不是包含code和data的完整响应
    const response: any = await request.delete(`/api/order-status/${statusId}`);

    // 由于request.ts自动解包，response直接就是后端返回的data部分
    // 对于DELETE请求，如果成功，后端会返回code: 200, msg: '...'，request.ts会解包data部分
    // 因此，response直接就是后端的data部分，对于成功删除，这可能是一个成功消息或undefined

    // 正确处理后端返回的格式：{code: 200, msg: '...', data: ...}
    // request.ts会自动解包data，所以response直接是解包后的数据
    // 但我们仍应检查是否有错误
    if (response && response.code === 200) {
      ElMessage.success(response.msg || '订单状态记录删除成功');
    } else {
      // 如果后端返回了错误格式
      ElMessage.success('订单状态记录删除成功'); // 即使response格式不标准，也认为是成功的
    }

    // 重新加载订单列表以更新状态
    await fetchOrders();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除订单状态记录失败:', error);
      ElMessage.error('删除订单状态记录失败');
    }
  }
};

// 跳转到带询盘详情的订单进度报告页面
const goToDetailedReport = (row: any) => {
  // 检查是否有订单状态ID
  if (row.status_id) {
    // 在新标签页中打开带询盘详情的报告页面
    const url = `/order-status-report?orderId=${row.status_id}&withInquiry=true`;
    window.open(url, '_blank');
  } else {
    ElMessage.warning('该订单尚无状态记录，无法生成报告');
  }
};

// 播放视频函数
const playVideo = (videoUrl: string) => {
  if (!videoUrl) {
    ElMessage.error('视频URL无效');
    return;
  }
  // 替换反斜杠为正斜杠
  const correctedUrl = videoUrl.replace(/\\/g, '/');
  currentVideoSrc.value = correctedUrl;
  showVideoPlayer.value = true;

  // 确保视频在打开后能够播放
  nextTick(() => {
    if (videoRef.value) {
      videoRef.value.play().catch(e => console.error('自动播放失败:', e));
    }
  });
};
// 从模板调用的包装函数，用于处理类型问题
const deleteImageFromTemplate = (task: any, imgIndex: number) => {
  const taskId = task?.id ? Number(task.id) : undefined;
  deleteImage(task, imgIndex, taskId);
};

// 删除媒体文件的包装函数（用于处理图片和视频）
const deleteMediaFromTemplate = (task: any, mediaIndex: number) => {
  const taskId = task?.id ? Number(task.id) : undefined;
  deleteMedia(task, mediaIndex, taskId);
};

// 删除媒体文件（图片或视频）
const deleteMedia = async (task: any, mediaIndex: number, taskId?: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个媒体文件吗？删除后将无法恢复。', '确认删除', {
      type: 'warning'
    });

    // 1. 解析当前媒体文件为结构化数组
    const currentMediaFiles = getTaskMediaFiles(task);

    // 2. 边界校验
    if (mediaIndex < 0 || mediaIndex >= currentMediaFiles.length) {
      ElMessage.error('媒体文件索引超出范围');
      return;
    }

    // 3. 获取要删除的媒体文件信息
    const mediaToDelete = currentMediaFiles[mediaIndex];
    const actualTaskId = taskId || (task.task_id ? Number(task.task_id) : undefined) || (task.id ? Number(task.id) : undefined);

    // 验证任务ID是否有效
    if (!actualTaskId) {
      ElMessage.error('无法删除媒体文件：任务ID无效');
      return;
    }

    // 4. 使用新的媒体文件ID进行删除
    let response;
    if (mediaToDelete.id) {
      // 使用新的媒体文件ID删除
      response = await request.delete(`/api/order-status/${currentOrderStatusId.value}/tasks/${actualTaskId}/media`, {
        data: { media_file_id: mediaToDelete.id }
      });
    } else {
      // 兼容旧数据，使用文件路径删除（虽然旧数据不适用于这个函数）
      ElMessage.error('无法删除媒体文件：缺少媒体文件ID');
      return;
    }


    // 5. 更新本地任务数据
    const taskIndex = tasks.value.findIndex(t =>
      Number(t.task_id || t.id || 0) === Number(actualTaskId || 0)
    );

    if (taskIndex > -1) {
      const newTasks = [...tasks.value];

      if (mediaToDelete.id) {
        // 从media_files数组中移除对应的媒体文件
        const updatedMediaFiles = newTasks[taskIndex].media_files?.filter((file: any) => file.id !== mediaToDelete.id) || [];

        newTasks[taskIndex] = {
          ...newTasks[taskIndex],
          media_files: updatedMediaFiles,
          images: updatedMediaFiles.filter((file: any) => file.file_type === 'image'),
          videos: updatedMediaFiles.filter((file: any) => file.file_type === 'video'),
          image_count: updatedMediaFiles.filter((file: any) => file.file_type === 'image').length,
          video_count: updatedMediaFiles.filter((file: any) => file.file_type === 'video').length
        };
      }

      tasks.value = newTasks;
    } else {
      console.warn('未找到对应的任务进行更新');
    }

    ElMessage.success('媒体文件删除成功');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除媒体文件失败:', error);
      ElMessage.error('删除媒体文件失败');
    }
  }
};

// 删除任务
const deleteTask = async (taskId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此任务吗？删除后将无法恢复，相关的图片也会被删除。', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    // 先查找任务，支持id和task_id两种查找方式
    let taskIndex = tasks.value.findIndex((task: any) => task.id === taskId);
    if (taskIndex === -1) {
      taskIndex = tasks.value.findIndex((task: any) => task.task_id === taskId);
    }

    if (taskIndex === -1) {
      ElMessage.error('任务不存在');
      return;
    }

    const task = tasks.value[taskIndex];
    const actualTaskId = task.id || task.task_id; // 使用实际的任务ID

    // 尝试从服务器删除
    try {
      await request.delete(`/api/order-status/${currentOrderStatusId.value}/tasks/${actualTaskId}`);

      // 服务器删除成功后，从本地移除任务
      tasks.value.splice(taskIndex, 1);
      ElMessage.success('任务删除成功');
    } catch (serverError) {
      // 检查错误类型
      if (serverError.response && serverError.response.status === 404) {
        // 服务器返回404，说明该任务可能不存在（可能已经被删除或未正确保存）
        // 仍然从本地移除任务
        tasks.value.splice(taskIndex, 1);
        ElMessage.success('任务已从本地移除');
      } else {
        // 其他服务器错误
        console.error('删除任务失败:', serverError);
        ElMessage.error('删除任务失败');
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error);
      ElMessage.error('删除任务失败');
    }
  }
};

// 清空全部状态数据（包括状态日志、任务项及关联文件）
const clearAllStatusData = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有状态数据吗？此操作将删除所有状态日志、任务项及相关文件，且无法恢复！',
      '危险操作确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    );

    if (!currentOrderStatusId.value) {
      ElMessage.error('当前没有选中的订单状态记录');
      return;
    }

    const response: any = await request.post(`/api/order-status/${currentOrderStatusId.value}/clear-all`);


    // 注意：由于request.ts会自动解包data，这里response已经是后端返回的data部分
    // 后端返回格式为 {code: 200, data: {...}, msg: "..."}，但前端接收到的是data部分
    // 所以这里直接认为请求成功（如果失败，request拦截器会抛出异常）
    ElMessage.success('清空成功');

    // 重新加载订单状态详情
    await loadOrderStatusDetails();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空全部状态数据失败:', error);
      ElMessage.error('清空失败');
    }
  }
};

// ===================== 优化loadOrderStatusDetails中的任务处理 =====================
const loadOrderStatusDetails = async () => {
  if (!selectedOrderDetail.value) return;

  const orderId = selectedOrderDetail.value.id;
  if (!orderId) return;

  try {
    const response: any = await request.get('/api/order-status', {
      params: { order_id: orderId }
    });

    if (response) {
      currentOrderStatusId.value = response.id;

      // 更新订单详情进度
      selectedOrderDetail.value = {
        ...selectedOrderDetail.value,
        completed_tasks: response.completed_tasks || 0,
        total_tasks: response.total_tasks || 0,
        progress_percent: response.progress_percent || 0
      };

      // 更新状态日志
      statusLogs.value = response.status_logs || [];

      // 处理任务数据
      const allTasks: any[] = [];
      (response.status || []).forEach((category: any) => {
        const statusLogId = category.status_log_id;
        (category.tasks || []).forEach((task: any) => {
          // 确保任务对象结构完整
          allTasks.push({
            id: task.task_id,
            task_id: task.task_id,
            name: task.name,
            category: task.category,
            description: task.description,
            is_completed: task.is_completed || false,
            // 包含新的媒体文件字段
            media_files: task.media_files || [],
            images: task.images || [],
            videos: task.videos || [],
            image_count: task.image_count || 0,
            video_count: task.video_count || 0,
            status_log_id: statusLogId,
            create_time: task.create_time,
            update_time: task.update_time,
            sort_order: task.sort || 0,
            parent_id: statusLogId,
            item_type: 'sub'
          });
        });
      });

      tasks.value = allTasks;

      // 初始化展开状态
      const newExpanded: {[key: number]: boolean} = {};
      statusLogs.value.forEach(log => {
        newExpanded[log.id] = expandedStatusLogs.value[log.id] || false;
      });
      expandedStatusLogs.value = newExpanded;

      // 新增：强制更新展开状态，触发UI重渲染
      expandedStatusLogs.value = { ...expandedStatusLogs.value };
    }
  } catch (error) {
    console.error('加载订单状态详情失败:', error);
  }
};

// ===================== 生命周期 =====================
// 组件挂载
onMounted(async () => {
  window.addEventListener('resize', handleResize);
  await fetchUserInfo();
  fetchOrders();
});

// 组件卸载
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  // 清理上传预览组件引用
  uploadPreviewRefs.value = {};
});

// 监听任务变化，自动更新订单列表进度
watch([() => tasks.value.length, () => tasks.value.map(t => t.is_completed)], () => {
  if (selectedOrderDetail.value && selectedOrderDetail.value.id) {
    // 找到对应订单并更新进度
    const orderIndex = orders.value.findIndex(o => o.id === selectedOrderDetail.value.id);
    if (orderIndex > -1) {
      const completedTasks = tasks.value.filter(t => t.is_completed).length;
      const totalTasks = tasks.value.length;
      const progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

      orders.value[orderIndex] = {
        ...orders.value[orderIndex],
        completed_tasks: completedTasks,
        total_tasks: totalTasks,
        progress_percent: progress
      };
    }
  }
}, { deep: true });



// ===================== 剪贴板功能 =====================



// 显示图片上传预览组件
const showImageUploadPreviewForTask = (taskId: number) => {
  currentImageUploadTaskId.value = taskId;
  showImageUploadPreview.value = true;
};

// ===================== 修改媒体上传成功回调 =====================

const onMediaUploadSuccess = async (files: File[], mediaFiles: any[] = []) => {

  ElMessage.success(`${files.length} 个媒体文件上传成功`);



  // 如果有返回的媒体文件信息，直接更新本地状态，避免重新加载

  if (mediaFiles && mediaFiles.length > 0) {

    // 更新本地任务数据中的媒体文件

    // 首先找到对应的task ID

    const currentTaskId = currentImageUploadTaskId.value;

    if (currentTaskId) {

      const taskIndex = tasks.value.findIndex(t =>

        Number(t.task_id || t.id || 0) === Number(currentTaskId || 0)

      );



      if (taskIndex > -1) {

        const newTasks = [...tasks.value];

        const currentTask = newTasks[taskIndex];



        // 将新上传的媒体文件添加到现有媒体文件列表中

        const updatedMediaFiles = [...(currentTask.media_files || []), ...mediaFiles];



        newTasks[taskIndex] = {

          ...currentTask,

          media_files: updatedMediaFiles,

          images: updatedMediaFiles.filter((file: any) => file.file_type === 'image'),

          videos: updatedMediaFiles.filter((file: any) => file.file_type === 'video'),

          image_count: updatedMediaFiles.filter((file: any) => file.file_type === 'image').length,

          video_count: updatedMediaFiles.filter((file: any) => file.file_type === 'video').length

        };



        tasks.value = newTasks;

      }

    } else {

      // 如果没有有效的任务ID，重新加载订单状态详情

      await loadOrderStatusDetails();

    }

  } else {

    // 如果没有返回媒体文件信息，则重新加载订单状态详情

    await loadOrderStatusDetails();

  }



  // 隐藏上传组件

  showImageUploadPreview.value = false;

  currentImageUploadTaskId.value = null;

};

// 媒体上传失败回调
const onMediaUploadFailure = (error: any) => {
  console.error('媒体文件上传失败：', error);
  ElMessage.error('媒体文件上传失败');
};

// 上传剪贴板媒体回调
const onUploadClipboardMedia = async (response: any, file: File, taskId: number) => {
  try {
    // 检查文件类型 - 支持图片和视频
    if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) {
      ElMessage.error('请选择图片或视频文件');
      return;
    }

    // 验证文件类型
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    const allowedImageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];
    const allowedVideoExts = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v'];

    if (!allowedImageExts.includes(ext) && !allowedVideoExts.includes(ext)) {
      ElMessage.error(`不支持的媒体格式：${ext}，支持的格式：${[...allowedImageExts, ...allowedVideoExts].join(', ')}`);
      return;
    }

    // 创建FormData对象
    const formData = new FormData();
    formData.append('file', file);
    formData.append('task_id', taskId.toString());

    const response: any = await request.post('/api/order-status/upload-multiple-images', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent: any) => {
        if (progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          // 这里可以显示上传进度，例如使用 ElMessage 或其他UI组件
        }
      }
    });

    if (response) {
      const fileType = file.type.startsWith('image/') ? '图片' : '视频';
      ElMessage.success(`剪贴板${fileType}上传成功`);

      // 使用返回的媒体文件信息更新本地状态
      if (response.data && response.data.media_files && response.data.media_files.length > 0) {
        // 从响应中获取新上传的媒体文件信息
        const newMediaFiles = response.data.media_files.map((mediaFile: any) => ({
          id: mediaFile.id,
          file_name: mediaFile.file_name || file.name,
          file_path: mediaFile.file_path,
          thumb_path: mediaFile.thumb_path,
          file_type: mediaFile.file_type,
          file_size: mediaFile.file_size,
          upload_time: mediaFile.upload_time
        }));

        // 更新本地任务数据中的媒体文件
        const taskIndex = tasks.value.findIndex(t =>
          Number(t.task_id || t.id || 0) === Number(taskId || 0)
        );

        if (taskIndex > -1) {
          const newTasks = [...tasks.value];
          const currentTask = newTasks[taskIndex];

          // 将新上传的媒体文件添加到现有媒体文件列表中
          const updatedMediaFiles = [...(currentTask.media_files || []), ...newMediaFiles];

          newTasks[taskIndex] = {
            ...currentTask,
            media_files: updatedMediaFiles,
            images: updatedMediaFiles.filter((file: any) => file.file_type === 'image'),
            videos: updatedMediaFiles.filter((file: any) => file.file_type === 'video'),
            image_count: updatedMediaFiles.filter((file: any) => file.file_type === 'image').length,
            video_count: updatedMediaFiles.filter((file: any) => file.file_type === 'video').length
          };
          tasks.value = newTasks;
        }
      } else {
        // 如果响应中没有媒体文件信息，则重新加载订单状态详情
        await loadOrderStatusDetails();
      }
    }
  } catch (error) {
    console.error('剪贴板媒体上传失败:', error);
    ElMessage.error('剪贴板媒体上传失败');
  }
};

/**
 * 设置上传预览组件引用
 */
const setUploadPreviewRef = (task: any) => {
  return (el: any) => {
    const taskId = getValidTaskId(task);
    if (!taskId) return;

    // 当el为null时，表示组件被卸载，应从引用中移除
    if (el) {
      uploadPreviewRefs.value[taskId] = el;
    } else {
      // 确保删除对应的任务ID引用
      delete uploadPreviewRefs.value[taskId];
    }
  };
};

/**
 * 处理输入框的粘贴事件
 */
const handleInputPaste = (e: ClipboardEvent, taskId: number | undefined) => {
  try {
    // 检查taskId是否有效
    if (!taskId) {
      ElMessage.error('无法粘贴媒体文件：未指定有效的任务ID');
      return;
    }

    let file = null;

    // 方案1：使用 clipboardData.items
    if (e.clipboardData && e.clipboardData.items) {
      for (let i = 0; i < e.clipboardData.items.length; i++) {
        const item = e.clipboardData.items[i];
        if (item.kind === 'file' && (item.type.startsWith('image/') || item.type.startsWith('video/'))) {
          file = item.getAsFile();
          break;
        }
      }
    }

    // 方案2：使用 clipboardData.files
    if (!file && e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
      const candidate = e.clipboardData.files[0];
      if (candidate.type.startsWith('image/') || candidate.type.startsWith('video/')) {
        file = candidate;
      }
    }

    if (file) {
      // 验证文件类型
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      const allowedImageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];
      const allowedVideoExts = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v'];

      if (allowedImageExts.includes(ext) || allowedVideoExts.includes(ext)) {
        // 查找对应的uploadPreviewRef并调用addClipboardMedia方法
        const uploadPreviewRef = uploadPreviewRefs.value[taskId];
        if (uploadPreviewRef && uploadPreviewRef.addClipboardMedia) {
          uploadPreviewRef.addClipboardMedia(file);
          const fileType = file.type.startsWith('image/') ? '图片' : '视频';
          ElMessage.success(`已检测到${fileType}: ${file.name}，已添加到上传队列...`);
        } else {
          console.warn('uploadPreviewRefs内容:', uploadPreviewRefs.value);
          console.warn('查找的任务ID:', taskId);
          console.warn('可用的任务ID:', Object.keys(uploadPreviewRefs.value));
          ElMessage.warning(`找不到任务ID为 ${taskId} 的上传组件，请确保该任务有上传组件`);
        }
      } else {
        ElMessage.warning(`检测到文件但格式不支持: ${ext}，仅支持: ${[...allowedImageExts, ...allowedVideoExts].join(', ')}`);
      }
    } else {
      // 检查是否是文本内容
      const pastedText = e.clipboardData?.getData('text') || '';
      if (pastedText) {
        ElMessage.info('检测到文本内容，此功能主要用于媒体文件粘贴');
      } else {
        ElMessage.warning('剪贴板中未检测到媒体文件');
      }
    }
  } catch (error) {
    console.warn('处理粘贴事件时出错:', error);
    ElMessage.error('处理粘贴事件失败');
  }
};
// ===================== 路由 =====================
</script>

<style scoped>
/* 基础容器样式 */
.order-status-container {
  padding: 10px;
}

/* 图标样式 */
.el-icon {
  padding: 8px 15px;
  color: white;
  border-radius: 5px;
  cursor: pointer;
}

.opera-btn{
  padding: 0px;
}

.btn-add-photo {
  color: gray;
  background-color: rgba(156, 156, 156, 0.1);
  font-size: 16px;
  margin-left: 15px;
}

.btn-add-task {
  padding: 6px 12px;
  color: gray;
  background-color: rgba(156, 156, 156, 0.3);
  font-size: 16px;
  margin-left: 15px;
}

.btn-del-status {
  background-color: #f56c6c;
  padding: 6px 12px;
  color: rgb(255, 255, 255);
  font-size: 16px;
  margin-left: 15px;
}

.btn-del-task {
  background-color: #ff8888;
  padding: 5px 10px;
  color: rgb(255, 255, 255);
  font-size: 12px;
  margin-left: 25px;
}

.btn-del-photo{
  background-color: #f56c6c;
  padding: 4px 8px;
  color: rgb(255, 255, 255);
  font-size: 14px;
  margin-left: 5px;
  border-radius: 3px;
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-header {
  display: flex;
  justify-content: space-between;
}

/* 进度容器 */
.progress-container {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 20px;
  padding: 5px 10px;
  background-color: rgba(156, 156, 156, 0.1);
  border-radius: 5px;
}

/* 订单列表区域 */
.order-list-section {
  margin-bottom: 15px;
}

/* 进度文本 */
.progress-text {
  font-size: 12px;
  color: #606266;
  text-align: center;
  width: 100%;
}

/* 分页样式 */
.pagination {
  margin-top: 15px;
  text-align: center;
}

/* 订单信息卡片 */
.order-info-card {
  margin-bottom: 15px;
}

/* 订单信息容器 */
.order-info-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.upload-container {
  display: flex;
  flex-direction: row;
  gap: 10px;
  padding: 10px;
  background-color: rgba(2, 0, 129, 0.08);
  margin: 5px;
  width: 400px;
  border-radius: 10px;
}

/* 底部操作区域 */
.bottom-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

/* 操作按钮组 */
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

/* 进度汇总文本 */
.progress-summary {
  font-size: 14px;
  color: #606266;
}

/* 图片预览对话框样式 */
.image-preview-dialog .el-dialog {
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-preview-dialog .el-dialog__body {
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 可点击编辑字段样式 */
.clickable-field {
  cursor: pointer;
  border: 1px dashed transparent;
  padding: 2px;
  border-radius: 3px;
}

.clickable-field:hover {
  border: 1px dashed #409eff;
  background-color: #f5f7fa;
}

/* 全屏加载遮罩 */
.fullscreen-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.loading-icon {
  font-size: 24px;
  animation: rotating 2s linear infinite;
  margin-bottom: 10px;
  display: block;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 表格行样式 */
:deep(.el-table .el-table__row) {
  cursor: pointer;
}

:deep(.el-table .el-table__row:hover > td) {
  background-color: #f5f7fa;
}

/* ===================== 移动端适配 ===================== */
@media (min-width: 768px) {
  .order-status-container {
    padding: 20px;
  }

  .order-list-section {
    margin-bottom: 20px;
  }

  .pagination {
    margin-top: 20px;
  }

  .order-info-card {
    margin-bottom: 20px;
  }

  .bottom-actions {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    margin-top: 20px;
    padding-top: 20px;
  }

  .action-buttons {
    gap: 10px;
    justify-content: flex-start;
  }
}

@media (max-width: 767px) {
  .el-descriptions__label {
    display: block;
    font-weight: bold;
    margin-bottom: 2px;
  }

  .el-descriptions__content {
    display: block;
    margin-top: 2px;
  }

  .el-table {
    font-size: 12px;
  }

  .el-table th,
  .el-table td {
    padding: 4px 0;
  }

  .el-button {
    font-size: 12px;
    padding: 6px 12px;
  }

  .el-radio {
    font-size: 12px;
  }

  .el-input__inner {
    font-size: 12px;
  }

  .action-buttons {
    flex-wrap: nowrap;
    overflow-x: auto;
    justify-content: flex-start;
    gap: 6px;
  }
}

.el-card {
  margin-bottom: 10px;
}

.sub-card {
  background-color: rgba(216, 213, 255, 0.1);
  border:rgba(0, 0, 0, 0.1) solid 1px;
  padding: 15px;
  border-radius: 3px;

}

.task-img-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(85px, 1fr));  /* 考虑边框和间距，设置为85px */
  gap: 10px;
  max-width: 100%;
  padding: 5px 10px;
  border:rgba(167, 167, 167, 0.1) solid 1px;
  background-color: rgba(167, 167, 167, 0.1);
  border-radius: 2px;
  /* 移除自动行高，统一用固定尺寸 */
  grid-auto-rows: 85px;
}

/* 状态日志卡片 */
.status-log-card {
  margin-bottom: 15px;
}

.status-log-card .el-card__header {
  cursor: pointer;
  padding: 12px 20px;
}

.status-log-card .el-card__body {
  padding: 15px;
}

/* 展开/折叠图标 */
.expand-icon {
  transition: transform 0.3s;
  margin:0px 25px;
  padding: 15px 5px;
  color: black;
  cursor: pointer;
  background-color: rgba(0, 0, 0, 0.1);
}

.expand-icon:hover{
  background-color: #ebeef5;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

/* 可点击编辑字段样式 */
.clickable-field {
  cursor: pointer;
  border: 1px dashed transparent;
  padding: 2px;
  border-radius: 3px;
}

.clickable-field:hover {
  border: 1px dashed #409eff;
  background-color: #f5f7fa;
}

/* 移动端适配 */
@media (min-width: 768px) {
  .status-log-card .el-card__header {
    padding: 12px 20px;
  }

  .status-log-card .el-card__body {
    padding: 20px;
  }
}

.card-title{
  font-weight: 400;
  font-size: 20px;
}

/* ============ 核心修复：缩略图样式 ============ */
/* 外层容器 - 用于承载操作按钮，不裁剪 */
.thumb-wrapper {
  position: relative !important;  /* 操作按钮的定位容器 */
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  width: 85px !important;         /* 与grid列宽匹配 */
  height: 85px !important;        /* 与grid行高匹配 */
  box-sizing: border-box !important;
}

/* 内层裁剪容器 - 只裁剪图片内容 */
.thumb-inner-container {
  width: 80px !important;         /* 图片显示尺寸 */
  height: 80px !important;        /* 图片显示尺寸 */
  border-radius: 5px !important;
  overflow: hidden !important;    /* 只裁剪图片，不影响外层按钮 */
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  box-sizing: border-box !important;
}

/* 图片/视频缩略图样式 - 彻底解决拉伸 */
.thumb-img, .video-thumb {
  box-sizing: border-box !important;
  width: 100% !important;         /* 宽度填满内层容器 */
  height: 100% !important;        /* 高度填满内层容器 */
  object-fit: cover !important;   /* 保持宽高比，填充容器 */
  object-position: center center !important; /* 居中裁剪 */
  border-radius: 5px !important;
  border: rgba(123, 175, 235, 0.2) solid 3px !important;
  display: block !important;      /* 确保是块级元素 */
  margin: 0 !important;
  padding: 0 !important;
  flex-shrink: 0 !important;
  /* 额外重置可能导致拉伸的属性 */
  min-width: unset !important;
  min-height: unset !important;
  max-width: unset !important;
  max-height: unset !important;
}

/* ============ 操作按钮样式修复 ============ */
/* 删除图片按钮样式 - 定位到外层容器 */
.delete-img-btn {
  position: absolute !important;
  top: 0px !important;            /* 调整位置，避免超出可视区域 */
  right: 0px !important;          /* 调整位置，避免超出可视区域 */
  width: 20px !important;
  height: 20px !important;
  padding: 0 !important;
  border-radius: 50% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 10 !important;
  background-color: #f56c6c !important;
  border: 1px solid white !important;
  transform: scale(0.8) !important;
  opacity: 0 !important;
  transition: opacity 0.3s ease !important;
}

.delete-img-btn .el-icon {
  font-size: 12px !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* hover时显示删除按钮 */
.thumb-wrapper:hover .delete-img-btn {
  opacity: 1 !important;
}

.delete-img-btn:hover {
  background-color: #ff5a5a !important;
}

/* 文件类型指示器 - 定位到外层容器 */
.file-type-indicator {
  position: absolute !important;
  top: 0px !important;            /* 调整位置，避免超出可视区域 */
  left: 0px !important;           /* 调整位置，避免超出可视区域 */
  width: 16px !important;
  height: 16px !important;
  background-color: #409eff !important;
  border-radius: 50% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 10 !important;
}

.file-type-indicator .el-icon {
  font-size: 10px !important;
  color: white !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* 视频播放覆盖层 */
.video-play-overlay {
  position: absolute !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
  background-color: rgba(0, 0, 0, 0.5) !important;
  border-radius: 50% !important;
  width: 24px !important;
  height: 24px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  cursor: pointer !important;
  opacity: 0 !important;
  transition: opacity 0.3s ease !important;
  z-index: 5 !important;
}

.thumb-wrapper:hover .video-play-overlay {
  opacity: 1 !important;
}

/* 简易视频播放模态框样式 */
.video-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 99999;
}

.video-modal-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 90vw;
  max-height: 90vh;
  z-index: 100000;
}

.video-player {
  max-width: 100%;
  max-height: 85vh;
  border-radius: 8px;
  background: #000;
}

.video-controls {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}

.close-btn {
  padding: 8px 16px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* 视频容器样式 */
.video-container {
  position: relative;
  display: inline-block;
}
</style>