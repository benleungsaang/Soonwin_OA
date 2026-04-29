<template>
  <div class="inquiry-list-container">
    <CommonHeader title="询盘管理" />

    <!-- 搜索和筛选 -->
    <el-card shadow="hover" class="filter-card">
      <el-form :model="searchForm" style="display: flex; ">
        <!-- 单一搜索框 -->
        <el-form-item label="内容搜索" style="min-width: 300px; flex: 1;">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索地区、来源、公司名、联系人、电话、邮箱、包装产品、需求类型"
            clearable
            @keyup.enter="searchInquiriesByContent"
          />
        </el-form-item>

        <el-form-item @click="searchInquiriesByContent">
            <el-icon class="opera-icon-big" style="color: white;background-color: #409eff;"><Search /></el-icon>
        </el-form-item>

        <!-- 日期筛选 -->
        <el-form-item label="询盘日期" style="min-width: 300px; margin-left: 20px; flex: 1;">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="onDateRangeChange"
          />
        </el-form-item>
        <el-form-item style="margin-left: 10px;">
          <el-icon class="opera-icon-big" style="color: white;background-color: #409eff;" @click="searchInquiriesByDate">
            <Search />
          </el-icon>
          <!-- <el-button @click="resetSearch">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button> -->
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作按钮 -->
    <div style="margin-bottom: 20px;">
      <el-button type="primary" @click="showAddInquiryDialog">
        <el-icon><Plus /></el-icon>
        新增询盘
      </el-button>
      <el-button @click="showInquiryLogs" v-if="isAdmin">
        <el-icon><Document /></el-icon>
        查看日志
      </el-button>
      <el-button @click="exportData">
        <el-icon><Download /></el-icon>
        导出数据
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-table
      :data="inquiries"
      style="width: 100%"
      v-loading="loading"
      :row-style="{ cursor: 'pointer' }"
      @row-click="viewInquiryById"
    >
      <el-table-column prop="creator_name" label="创建人" width="120" />
      <el-table-column prop="area" label="地区" width="120" />
      <el-table-column prop="inquiry_date" label="询盘日期" width="120" />
      <el-table-column prop="inquiry_source" label="询盘来源" width="120" />
      <el-table-column prop="company_name" label="公司名" width="150" show-overflow-tooltip />
      <el-table-column prop="contact_person" label="联系人" width="120" />
      <el-table-column prop="phone" label="电话" width="130" />
      <el-table-column prop="email" label="邮箱" width="180" show-overflow-tooltip />
      <el-table-column prop="packaging_product" label="包装产品" width="150" show-overflow-tooltip />
      <el-table-column prop="machine_type" label="需求机器类型" show-overflow-tooltip />
      <el-table-column prop="create_time" label="创建时间" width="150" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="scope">
          <!-- <el-icon
            class="opera-icon"
            style="cursor: pointer; margin-right: 8px;color: white; background-color: #409eff;"
            @click.stop="viewInquiry(scope.row.id)">
            <View />
          </el-icon> -->

          <el-icon
            class="opera-icon"
            :style="!scope.row.is_associated ? 'cursor: pointer; margin-right: 8px;color: white; background-color: #409eff;' : 'cursor: not-allowed; margin-right: 8px;color: #ccc; background-color: #e6e6e6;'"
            @click.stop="!scope.row.is_associated && createOrder(scope.row)"
          >
            <Plus />
          </el-icon>
          <el-icon
            class="opera-icon"
            style="cursor: pointer;color: white; background-color: #f56c6c;"
            @click.stop="deleteInquiry(scope.row.id)">
            <Delete />
          </el-icon>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination" style="margin-top: 20px; display: flex; justify-content: center;">
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
      />
    </div>

    <!-- 新增/编辑询盘对话框 -->
    <el-dialog :title="inquiryDialogTitle" v-model="inquiryDialogVisible" width="70%" :before-close="handleDialogClose">
      <el-form :model="inquiryForm" :rules="inquiryRules" ref="inquiryFormRef" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="地区" prop="area">
              <el-autocomplete
                v-model="inquiryForm.area"
                :fetch-suggestions="queryArea"
                placeholder="请输入或选择地区"
                clearable
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="询盘日期" prop="inquiry_date">
              <el-date-picker
                v-model="inquiryForm.inquiry_date"
                type="date"
                placeholder="选择日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="询盘来源" prop="inquiry_source">
              <el-autocomplete
                v-model="inquiryForm.inquiry_source"
                :fetch-suggestions="querySource"
                placeholder="请输入或选择询盘来源"
                clearable
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="公司名" prop="company_name">
              <el-input v-model="inquiryForm.company_name" placeholder="请输入公司名" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="联系人" prop="contact_person">
              <el-input v-model="inquiryForm.contact_person" placeholder="请输入联系人" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话" prop="phone">
              <el-input v-model="inquiryForm.phone" placeholder="请输入电话" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="inquiryForm.email" placeholder="请输入邮箱" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="包装产品" prop="packaging_product">
              <el-input v-model="inquiryForm.packaging_product" placeholder="请输入包装产品" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="需求机器类型" prop="machine_type">
              <el-input
                v-model="inquiryForm.machine_type"
                type="textarea"
                :rows="2"
                placeholder="请输入需求机器类型"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 负责业务员选择（仅管理员和运营专员可见） -->
        <el-row :gutter="20" v-if="isAdmin || isOps">
          <el-col :span="24">
            <el-form-item label="分配负责业务员">
              <el-select
                v-model="inquiryForm.follower_id"
                placeholder="请选择负责业务员"
                clearable
                filterable
                style="width: 100%;"
              >
                <el-option
                  v-for="follower in followers"
                  :key="follower.emp_id"
                  :label="follower.name + ' (' + follower.emp_id + ')'"
                  :value="follower.emp_id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 按钮区域 -->
        <el-row :gutter="20" style="margin-top: 20px;">
          <el-col :span="24">
            <el-form-item>
              <el-button @click="cancelInquiry">取消</el-button>
              <el-button
                v-if="inquiryDialogTitle === '查看详情/编辑' || inquiryDialogTitle === '新增询盘'"
                type="primary"
                @click="submitInquiry"
                :loading="submitting"
              >
                提交
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

              <!-- 沟通记录部分 -->
              <div v-if="inquiryForm.id" class="communication-section">
                <el-divider />
                <div class="communication-header">
                  <h3>沟通记录 ({{ communications.length }})</h3>
                  <div style="display: flex; gap: 10px;">
                    <el-dropdown trigger="click" @command="handleCustomerDropdownCommand">
                      <el-button type="success" size="large">
                        登记客户信息
                        <el-icon style="margin-left: 5px;"><ArrowDown /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="create">创建新客户</el-dropdown-item>
                          <el-dropdown-item command="bind">绑定到现有客户</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                    <el-button type="primary" size="large" @click="showAddCommunicationDialog">
                      添加沟通记录
                      <el-icon style="margin-left: 5px;font-size: 20px;"><ChatLineRound /></el-icon>
                    </el-button>
                  </div>
                </div>

                        <!-- 沟通记录列表 -->

                        <div class="communication-list">

                          <el-card

                            v-for="comm in communications"

                            :key="comm.id"

                            class="communication-item"

                            shadow="hover"

                            body-style="padding:10px"

                          >

                            <div class="communication-content-header">

                              <span class="subject">主题：{{ comm.subject }}</span>

                              <div class="communication-footer"><span class="creator">{{ comm.creator_name }}</span>

                                <span class="time">{{ comm.create_time }}</span>

                                <el-icon @click="editCommunication(comm)" class="el-icon edit"><Edit /></el-icon>

                                <el-icon @click="deleteCommunication(comm.id)" class="el-icon delete"><Delete /></el-icon>

                              </div>

                            </div>

                            <!-- <div class="communication-company" v-if="comm.company_name">公司：{{ comm.company_name }}</div> -->

                            <div class="communication-content">{{ comm.content }}</div>



                            <!-- 沟通记录的图片附件 -->

                            <div v-if="getCommunicationMediaFiles(comm).length > 0" class="communication-media-container">

                              <div class="task-img-container">

                                <div

                                  v-for="(media, mediaIndex) in getCommunicationMediaFiles(comm)"

                                  :key="`comm-media-${comm.id}-${mediaIndex}`"

                                  class="thumb-wrapper"

                                >

                                  <!-- 内层容器：裁剪图片内容 -->

                                  <div class="thumb-inner-container">

                                    <!-- 图片文件显示 -->

                                    <el-image

                                      v-if="media.file_type === 'image'"

                                      :src="media.thumb || media.url"

                                      :preview-src-list="getCommunicationMediaUrls(comm)"

                                      :initial-index="Number(mediaIndex)"

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

                                    @click="deleteMediaFromCommunication(comm, Number(mediaIndex))"

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

                              </div>

                            </div>

                          </el-card>

                          <div v-if="communications.length === 0" class="no-communications">

                            暂无沟通记录

                          </div>

                        </div>
              </div>
      <template #footer>
        <span class="dialog-footer">
          <!-- 这里不放按钮，按钮已移到表单内部 -->
        </span>
      </template>
    </el-dialog>
          <!-- 新增/编辑沟通记录对话框 -->
          <el-dialog :title="communicationDialogTitle" v-model="addCommunicationDialogVisible" width="60%" class="communication-media-dialog">
            <el-form :model="communicationForm" :rules="communicationRules" ref="communicationFormRef" label-width="100px">
              <el-form-item label="主题" prop="subject">
                <el-input v-model="communicationForm.subject" placeholder="请输入沟通主题" />
              </el-form-item>
              <el-form-item label="内容" prop="content">
                <el-input
                  v-model="communicationForm.content"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入沟通内容"
                />
              </el-form-item>
              <el-form-item label="沟通日期" prop="communication_date">
                <el-date-picker
                  v-model="communicationForm.communication_date"
                  type="date"
                  placeholder="选择日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%;"
                />
              </el-form-item>

              <!-- 多媒体上传功能 -->
              <el-form-item label="附件上传" class="media-upload-full-width">
                <div style="display: flex; align-items: center; gap: 5px; flex-wrap: wrap;">
                  <el-tooltip content="可直接拖入图片或视频" placement="bottom">
                    <ImageUploadPreview
                      :ref="setCommunicationUploadPreviewRef"
                      :communication-id="currentCommunicationId"
                      :upload-path="`/api/inquiries/upload-communication-media`"
                      @upload-success="onCommunicationMediaUploadSuccess"
                      @upload-failure="onCommunicationMediaUploadFailure"
                      @upload-clipboard-image="onUploadClipboardCommunicationMedia"
                    />
                  </el-tooltip>
                  <el-tooltip content="点击输入框后按CTRL+V，可以粘贴剪切的图片" placement="bottom">
                    <el-input
                      style="width:130px;"
                      @paste="(e) => handleCommunicationInputPaste(e)"
                      placeholder="粘贴图片(Ctrl+V)"
                    ></el-input>
                  </el-tooltip>
                </div>

                <!-- 已上传的媒体文件列表 -->
                <div v-if="currentCommunicationMediaFiles.length > 0" class="communication-media-container">
                  <div class="task-img-container">
                    <div
                      v-for="(media, mediaIndex) in currentCommunicationMediaFiles"
                      :key="`current-comm-media-${mediaIndex}`"
                      class="thumb-wrapper"
                    >
                      <!-- 内层容器：裁剪图片内容 -->
                      <div class="thumb-inner-container">
                        <!-- 图片文件显示 -->
                        <el-image
                          v-if="media.file_type === 'image'"
                          :src="media.thumb || media.url"
                          :preview-src-list="getCommunicationMediaUrls('current')"
                                                                :initial-index="Number(mediaIndex)"                          preview-teleported
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
                        @click="deleteCurrentCommunicationMedia(mediaIndex)"
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
                  </div>
                </div>
              </el-form-item>
            </el-form>
            <template #footer>
              <span class="dialog-footer">
                <el-button @click="cancelCommunication">取消</el-button>
                <el-button type="primary" @click="submitCommunication" :loading="communicationSubmitting">确定</el-button>
              </span>
            </template>
          </el-dialog>
    <!-- 沟通记录对话框 -->
    <el-dialog title="沟通记录" v-model="communicationDialogVisible" width="70%">
      <div>
        <el-button type="primary" size="small" @click="showAddCommunicationDialog" style="margin-bottom: 20px;"><el-icon><ChatLineRound /></el-icon>添加沟通记录</el-button>

        <el-table :data="communications" style="width: 100%; margin-bottom: 20px;">
          <el-table-column prop="subject" label="主题" width="150" />
          <el-table-column prop="content" label="内容" width="200" />
          <el-table-column prop="company_name" label="公司名" width="150" />
          <el-table-column prop="communication_date" label="沟通日期" width="120" />
          <el-table-column prop="creator_name" label="创建人" width="120" />
          <el-table-column prop="create_time" label="创建时间" width="150" />
          <el-table-column label="操作" width="150">
            <template #default="scope">
              <el-button size="small" @click="editCommunication(scope.row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteCommunication(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeCommunicationDialog">关闭</el-button>
        </span>
      </template>


      </el-dialog>
        <!-- 引入通用日志对话框组件 -->
        <CommonLogDialog
          v-model="logDialogVisible"
          log-type="inquiry"
          :handle-jump="handleLogJump"
        />

        <!-- 删除失败提示模态框 -->
        <el-dialog
          title="删除失败"
          v-model="deleteFailDialogVisible"
          width="60%"
          :close-on-click-modal="false"
        >
          <div>
            <p style="color: #f56c6c; margin-bottom: 15px;">
              <el-icon><Warning /></el-icon>
              该询盘已关联订单，无法删除！
            </p>
            <p>关联的订单信息如下：</p>
            <el-table
              :data="associatedOrders"
              style="width: 100%; margin-top: 10px;"
              border
            >
              <el-table-column prop="id" label="订单ID" width="80" />
              <el-table-column prop="contract_no" label="合同编号" width="150" />
              <el-table-column prop="customer_name" label="客户名称" width="200" />
              <el-table-column prop="order_time" label="下单时间" width="120" />
              <el-table-column prop="contract_amount" label="合同金额" width="120">
                <template #default="scope">
                  ¥{{ scope.row.contract_amount ? scope.row.contract_amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00' }}
                </template>
              </el-table-column>
            </el-table>
          </div>
          <template #footer>
            <span class="dialog-footer">
              <el-button type="primary" @click="deleteFailDialogVisible = false">确定</el-button>
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

    <!-- 创建客户对话框 -->
    <el-dialog
      title="创建客户"
      v-model="createCustomerDialogVisible"
      width="500px"
    >
      <el-form :model="createCustomerForm" label-width="100px">
        <el-form-item label="公司名称">
          <el-input v-model="createCustomerForm.company_name" placeholder="请输入公司名称" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="createCustomerForm.contact_person" placeholder="请输入联系人" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="createCustomerForm.phone" placeholder="请输入电话" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="createCustomerForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="地区">
          <el-input v-model="createCustomerForm.area" placeholder="请输入地区" />
        </el-form-item>
        <el-form-item label="客户类型">
          <el-select v-model="createCustomerForm.customer_type" placeholder="请选择客户类型" style="width: 100%">
            <el-option label="经销商" value="经销商" />
            <el-option label="终端" value="终端" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createCustomerForm.remark" type="textarea" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createCustomerDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCreateCustomer" :loading="createCustomerSubmitting">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 绑定客户对话框 -->
    <el-dialog
      title="绑定客户"
      v-model="bindCustomerDialogVisible"
      width="700px"
    >
      <p style="color: #909399; margin-bottom: 10px;">选择一个客户进行绑定</p>
      <el-table
        :data="bindableCustomers"
        v-loading="bindableCustomersLoading"
        style="width: 100%"
        stripe
        border
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', textAlign: 'center' }"
        :cell-style="{ textAlign: 'center' }"
        @row-click="handleBindableCustomerRowClick"
        :row-class-name="getBindableCustomerRowClassName"
        :row-style="{ cursor: 'pointer' }"
      >
        <el-table-column width="60" label="选择">
          <template #default="scope">
            <el-radio v-model="selectedBindableCustomerId" :label="scope.row.id" @click.stop>&nbsp;</el-radio>
          </template>
        </el-table-column>
        <el-table-column prop="company_name" label="公司名" />
        <el-table-column prop="contact_person" label="联系人" />
        <el-table-column prop="phone" label="电话" />
        <el-table-column prop="area" label="地区" />
      </el-table>
      <el-pagination
        v-model:current-page="bindableCustomersPage"
        :page-size="bindableCustomersSize"
        :total="bindableCustomersTotal"
        layout="prev, pager, next"
        @current-change="loadBindableCustomers"
        style="margin-top: 10px; justify-content: center"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="bindCustomerDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmBindCustomer" :disabled="!selectedBindableCustomerId">确认绑定</el-button>
        </span>
      </template>
    </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRouter, useRoute } from 'vue-router';
import request from '@/utils/request';
import axios from 'axios';
import { Delete, Edit, ChatLineRound, View, Search, Plus, Document, Download, Refresh, Loading, OfficeBuilding, Warning, Close, VideoPlay, VideoCamera, User, ArrowDown } from '@element-plus/icons-vue';
import { formatBusinessLog } from '@/utils/logFormatter';
import CommonHeader from '@/components/CommonHeader.vue';
import CommonLogDialog from '@/components/CommonLogDialog.vue';
import ImageUploadPreview from '@/components/ImageUploadPreview.vue';
import { getCurrentUserRole } from '@/utils/authUtils';
import { createCustomerFromInquiry } from '@/api/customer'
import { bindInquiry } from '@/api/customer';

// 路由
const router = useRouter();
const route = useRoute();

// 检查当前用户是否为管理员
const isAdmin = computed(() => {
  const userRole = getCurrentUserRole();
  return userRole === 'admin';
});

// 检查当前用户是否为运营专员
const isOps = computed(() => {
  const userRole = getCurrentUserRole();
  return userRole === 'ops';
});

// 跟单专员列表
const followers = ref<any[]>([]);

// 在组件挂载时检查用户角色
// 用户角色检查现在通过computed属性自动处理
onMounted(async () => {
  // 加载询盘列表，同时获取所有可能需要的地区信息
  await loadInquiries();

  // 获取预设地区列表 - 从已加载的数据中提取，而不是再次请求
  try {
    // 使用已加载的询盘数据来填充地区列表
    // 如果需要完整列表，可以单独获取，但目前我们只需要获取一次数据
    if (inquiries.value && inquiries.value.length > 0) {
      const areas = [...new Set(inquiries.value.map((item: any) => item.area).filter((area: any) => area))];
      presetAreas.value = areas;
    }
  } catch (error) {
    console.error('提取地区列表失败:', error);
    // 出错时使用空数组
    presetAreas.value = [];
  }

  // 根据路由参数决定是否打开新增或编辑对话框
  if (route.name === 'inquiryCreate') {
    showAddInquiryDialog();
  } else if (route.name === 'inquiryEdit' && route.params.id) {
    viewInquiry(Number(route.params.id));
  }

  // 加载跟单专员列表（仅管理员和运营专员需要）
  if (isAdmin.value || isOps.value) {
    loadFollowers();
  }
});

// 监听路由变化，当路由参数变化时自动打开相应的对话框
watch(
  () => route.params.id,
  (newId) => {
    if (route.name === 'inquiryEdit' && newId) {
      viewInquiry(Number(newId));
    }
  }
);

watch(
  () => route.name,
  (newName) => {
    if (newName === 'inquiryCreate' && !inquiryDialogVisible.value) {
      showAddInquiryDialog();
    }
  }
);

// 分页参数
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

// 搜索参数
const searchForm = ref({
  search: '',  // 新增综合搜索字段
  area: '',
  contact_person: '',
  company_name: '',
  packaging_product: '',
  machine_type: '',
  inquiry_source: '',
  start_date: '',
  end_date: ''
});

// 日期范围
const dateRange = ref<[string, string] | null>(null);

// 数据
const inquiries = ref<any[]>([]);
const loading = ref(false);

// 预设地区和来源
const presetAreas = ref<string[]>([]);
const presetSources = ref(['官网', '阿里', '展会', '朋友介绍']);
// 用于存储打开对话框时的初始表单值
const initialInquiryForm = ref<any>(null);

// 询盘表单相关
const inquiryDialogVisible = ref(false);
const inquiryDialogTitle = ref('');
const editingInquiryId = ref<number | null>(null);
const submitting = ref(false);

const inquiryForm = ref({
  id: null as number | null,
  area: '',
  inquiry_date: '',
  inquiry_source: '',
  company_name: '',
  contact_person: '',
  phone: '',
  email: '',
  packaging_product: '',
  machine_type: '',
  follower_id: '',  // 添加跟单专员ID字段
  customer_id: null as number | null, // 关联的客户ID
  is_associated: false // 是否已关联订单
});

// 沟通记录相关
const communicationDialogVisible = ref(false);
const communications = ref<any[]>([]);
const currentInquiryId = ref<number | null>(null);

const addCommunicationDialogVisible = ref(false);
const communicationDialogTitle = ref('');
const editingCommunicationId = ref<number | null>(null);
const communicationSubmitting = ref(false);

const communicationForm = ref({
  id: null as number | null,
  subject: '',
  content: '',
  communication_date: '',
  company_name: ''
});

// 沟通记录媒体文件相关
const currentCommunicationId = ref<number | null>(null); // 用于标识当前编辑的沟通记录
const currentCommunicationMediaFiles = ref<any[]>([]); // 当前沟通记录的媒体文件
const pendingMediaFiles = ref<File[]>([]); // 待上传的媒体文件
const communicationUploadPreviewRefs = ref<{[key: number]: any}>({}); // 存储通信图片上传预览组件引用

// 用于跟踪媒体文件的上传状态
const mediaUploadStatus = ref<{[key: number]: any}>({}); // 用于跟踪每个沟通记录的媒体文件

// 通用日志组件相关
const logDialogVisible = ref(false);

// 删除失败提示相关
const deleteFailDialogVisible = ref(false);
const associatedOrders = ref<any[]>([]);

// 视频播放相关
const showVideoPlayer = ref(false);
const currentVideoSrc = ref('');
const videoRef = ref<HTMLVideoElement | null>(null);

// 表单引用
const inquiryFormRef = ref();
const communicationFormRef = ref();

// 表单验证规则 - 初始为空数组，通过setValidationRules函数动态设置
const inquiryRules = ref({
  area: [],
  inquiry_date: [],
  inquiry_source: [],
  company_name: [],
  contact_person: [],
  phone: [],
  email: [],
  packaging_product: [],
  machine_type: []
});

// 动态设置验证规则 - 根据是否为编辑模式决定是否启用验证
const setValidationRules = (isEditing: boolean = false) => {
  if (isEditing) {
    // 编辑模式下启用完整验证
    inquiryRules.value = {
      area: [
        { required: true, message: '请输入地区', trigger: 'blur' }
      ],
      inquiry_date: [
        { required: true, message: '请选择询盘日期', trigger: 'change' }
      ],
      inquiry_source: [
        { required: true, message: '请输入询盘来源', trigger: 'blur' }
      ],
      company_name: [
        { required: true, message: '请输入公司名称', trigger: 'blur' }
      ],
      contact_person: [
        { required: true, message: '请输入联系人', trigger: 'blur' }
      ],
      phone: [
        { required: true, message: '请输入电话', trigger: 'blur' }
      ],
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        {
          type: 'email',
          message: '请输入正确的邮箱格式',
          trigger: 'blur'
        }
      ],
      packaging_product: [
        { required: true, message: '请输入包装产品', trigger: 'blur' }
      ],
      machine_type: [
        { required: true, message: '请输入需求机器类型', trigger: 'blur' }
      ]
    };
  } else {
    // 新增模式下不设置验证规则（只在提交时验证）
    inquiryRules.value = {
      area: [],
      inquiry_date: [],
      inquiry_source: [],
      company_name: [],
      contact_person: [],
      phone: [],
      email: [],
      packaging_product: [],
      machine_type: []
    };
  }
};

// 初始化验证规则为不启用状态（新增模式）
setValidationRules(false);

const communicationRules = {
  subject: [
    { required: true, message: '请输入沟通主题', trigger: 'blur' }
  ]
};

  // 加载销售员工列表
const loadFollowers = async () => {
  try {
    const response = await request.get('/api/users/sales-employees');
    followers.value = response.list || response.data?.list || [];
  } catch (error) {
    console.error('加载销售员工列表失败:', error);
    // 如果新的API失败，回退到原来的逻辑
    try {
      const response = await request.get('/api/employees');
      const allEmployees = response.list || response.data || [];
      // 过滤出角色为sales的员工
      followers.value = allEmployees.filter((emp: any) =>
        emp.user_role === 'sales'
      );
    } catch (fallbackError) {
      console.error('加载员工列表作为备选失败:', fallbackError);
      followers.value = [];
    }
  }
};

  // 显示新增询盘对话框
const showAddInquiryDialog = () => {
  inquiryDialogTitle.value = '新增询盘';
  editingInquiryId.value = null;
  const emptyForm = {
    id: null,
    area: '',
    inquiry_date: '',
    inquiry_source: '',
    company_name: '',
    contact_person: '',
    phone: '',
    email: '',
    packaging_product: '',
    machine_type: '',
    follower_id: '',
    customer_id: null,
    is_associated: false
  };
  inquiryForm.value = { ...emptyForm };
  // 保存初始表单值用于比较
  initialInquiryForm.value = JSON.parse(JSON.stringify(emptyForm));
  // 设置验证规则：新增模式下不启用实时验证
  setValidationRules(false);
  inquiryDialogVisible.value = true;
};


// 查看询盘详情（支持编辑）
const viewInquiry = async (id: number) => {
  try {
    // 使用axios直接请求，避免拦截器的错误处理
    const token = localStorage.getItem('oa_token');
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL || '/' }api/inquiries/${id}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    // 检查响应是否成功
    if (response.data && response.data.code === 200) {
      const responseData = response.data.data; // 获取实际数据
      // 确保follower_id字段存在，并确保is_associated字段存在
      const inquiryData = {
        ...responseData,
        follower_id: responseData.follower_id || '',
        is_associated: responseData.is_associated || false
      };
      inquiryForm.value = inquiryData;
      // 保存初始表单值用于比较
      initialInquiryForm.value = JSON.parse(JSON.stringify(inquiryData));
      editingInquiryId.value = id;
      inquiryDialogTitle.value = '查看详情/编辑';
      // 加载沟通记录
      await loadCommunications(id);
      // 设置验证规则：编辑模式下启用验证
      setValidationRules(true);
      inquiryDialogVisible.value = true;
    } else {
      // 如果后端返回了错误格式的响应
      if (response.data && response.data.code !== 200 &&
          response.data.msg && (response.data.msg.includes('404') || response.data.msg.toLowerCase().includes('not found'))) {
        ElMessage.error('该询盘已删除或不存在');
      } else {
        ElMessage.error('加载询盘详情失败');
      }
    }
  } catch (error: any) {
    console.error('加载询盘详情失败:', error);
    // 检查错误是否为404相关的错误
    if (error && error.response) {
      const responseData = error.response.data;
      if (responseData && typeof responseData === 'object' &&
          responseData.msg && (responseData.msg.includes('404') || responseData.msg.toLowerCase().includes('not found'))) {
        ElMessage.error('该询盘已删除或不存在');
      } else {
        ElMessage.error('加载询盘详情失败');
      }
    } else {
      ElMessage.error('加载询盘详情失败');
    }
  }
};

// 通过行点击查看详情
const viewInquiryById = (row: any) => {
  viewInquiry(row.id);
};

// 提交询盘
const submitInquiry = async () => {
  if (!inquiryFormRef.value) return;

  // 如果是编辑现有询盘且表单未被修改，则直接关闭
  if (editingInquiryId.value && !isFormChanged()) {
    ElMessage.info('表单内容未修改，无需提交');
    inquiryDialogVisible.value = false;
    return;
  }

  // 在提交前启用完整验证规则
  setValidationRules(true);

  // 等待DOM更新后执行验证
  await nextTick();

  await inquiryFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitting.value = true;
      try {
        let response;
        if (editingInquiryId.value) {
          // 更新现有询盘
          response = await request.put(`/api/inquiries/${editingInquiryId.value}`, inquiryForm.value);
          ElMessage.success('询盘更新成功');
        } else {
          // 创建新询盘
          response = await request.post('/api/inquiries', inquiryForm.value);
          ElMessage.success('询盘创建成功');
        }

        // 关闭对话框并重新加载列表
        inquiryDialogVisible.value = false;
        loadInquiries();
      } catch (error) {
        console.error('提交询盘失败:', error);
        ElMessage.error('提交询盘失败');
      } finally {
        submitting.value = false;
      }
    } else {
      ElMessage.error('请填写必填项');
    }
  });
};
// 取消询盘操作
const cancelInquiry = () => {
  // 如果表单没有被修改过，直接关闭
  if (!isFormChanged()) {
    inquiryDialogVisible.value = false;
    return;
  }

  ElMessageBox.confirm('表单内容已修改，确认取消？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
  .then(() => {
    inquiryDialogVisible.value = false;
  })
  .catch(() => {
    // 取消操作
  });
};



// 删除询盘
const deleteInquiry = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这条询盘记录吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await request.delete(`/api/inquiries/${id}`);
    ElMessage.success('询盘删除成功');
    loadInquiries();
  } catch (error: any) {
    console.error('删除询盘失败:', error);
    if (error !== 'cancel') {
      // 检查错误响应是否包含关联订单信息
      if (error.response && error.response.data && error.response.data.data && error.response.data.data.associated_orders) {
        // 显示删除失败的模态框，包含关联订单信息
        associatedOrders.value = error.response.data.data.associated_orders;
        deleteFailDialogVisible.value = true;
      } else {
        ElMessage.error(error.response?.data?.msg || '删除询盘失败');
      }
    }
  }
};

// 创建客户
const createCustomerDialogVisible = ref(false)
const createCustomerForm = ref({
  company_name: '',
  contact_person: '',
  phone: '',
  email: '',
  area: '',
  customer_type: '',
  remark: ''
})
const createCustomerSubmitting = ref(false)
const currentInquiryForCustomer = ref<any>(null)

// 绑定客户相关
const bindCustomerDialogVisible = ref(false)
const bindableCustomers = ref<any[]>([])
const bindableCustomersLoading = ref(false)
const bindableCustomersPage = ref(1)
const bindableCustomersSize = ref(10)
const bindableCustomersTotal = ref(0)
const selectedBindableCustomerId = ref<number | null>(null)
const selectedBindableCustomer = ref<any>(null)

const createCustomer = async (row: any) => {
  currentInquiryForCustomer.value = row
  createCustomerForm.value = {
    company_name: row.company_name || '',
    contact_person: row.contact_person || '',
    phone: row.phone || '',
    email: row.email || '',
    area: row.area || '',
    customer_type: '',
    remark: ''
  }
  createCustomerDialogVisible.value = true
}

const submitCreateCustomer = async () => {
  try {
    createCustomerSubmitting.value = true
    const result = await createCustomerFromInquiry(currentInquiryForCustomer.value.id, createCustomerForm.value)
    ElMessage.success('创建客户成功')
    createCustomerDialogVisible.value = false
    loadInquiries()
    // 跳转到客户信息页面
    if (result && result.id) {
      router.push('/customer-management')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '创建客户失败')
  } finally {
    createCustomerSubmitting.value = false
  }
}

// 显示绑定客户对话框 - 创建新客户
const showBindCustomerDialog = async () => {
  // 设置当前询盘用于后续创建客户时关联
  currentInquiryForCustomer.value = inquiryForm.value
  // 填充询盘信息到创建客户表单
  createCustomerForm.value = {
    company_name: inquiryForm.value.company_name || '',
    contact_person: inquiryForm.value.contact_person || '',
    phone: inquiryForm.value.phone || '',
    email: inquiryForm.value.email || '',
    area: inquiryForm.value.area || '',
    customer_type: '',
    remark: ''
  }
  createCustomerDialogVisible.value = true
}

// 显示绑定到已有客户对话框
const showBindToExistingCustomerDialog = async () => {
  selectedBindableCustomerId.value = null
  selectedBindableCustomer.value = null
  bindCustomerDialogVisible.value = true
  await loadBindableCustomers()
}

// 处理客户下拉菜单命令
const handleCustomerDropdownCommand = (command: string) => {
  if (command === 'create') {
    showBindCustomerDialog()
  } else if (command === 'bind') {
    showBindToExistingCustomerDialog()
  }
}

const loadBindableCustomers = async () => {
  try {
    bindableCustomersLoading.value = true
    const response: any = await request.get('/api/customers', {
      params: { page: bindableCustomersPage.value, size: bindableCustomersSize.value }
    })
    // 过滤掉当前询盘已关联的客户
    bindableCustomers.value = (response.list || []).filter((item: any) =>
      item.id !== inquiryForm.value.customer_id
    )
    bindableCustomersTotal.value = response.total || 0
  } catch (error) {
    console.error('获取可绑定客户列表失败:', error)
  } finally {
    bindableCustomersLoading.value = false
  }
}

const handleBindableCustomerRowClick = (row: any) => {
  selectedBindableCustomerId.value = row.id
  selectedBindableCustomer.value = row
}

const getBindableCustomerRowClassName = ({ row }: { row: any }) => {
  return selectedBindableCustomerId.value === row.id ? 'selected-row' : ''
}

const confirmBindCustomer = async () => {
  if (!selectedBindableCustomerId.value || !editingInquiryId.value) return
  try {
    await bindInquiry(selectedBindableCustomerId.value, editingInquiryId.value)
    ElMessage.success('绑定客户成功')
    bindCustomerDialogVisible.value = false
    loadInquiries()
    // 如果当前正在查看询盘详情，刷新当前数据
    if (editingInquiryId.value) {
      await viewInquiry(editingInquiryId.value)
    }
  } catch (error: any) {
    ElMessage.error(error.message || '绑定客户失败')
  }
}

// 跳转到客户详情
const goToCustomer = (customerId: number) => {
  router.push('/customer-management')
}

// 格式化操作详情为易读文本
const formatOperationDetailsForLog = (log: any) => {
  try {
    return formatBusinessLog(log);
  } catch (error) {
    console.error('格式化日志详情失败:', error);
    // 如果格式化失败，返回原始操作详情
    if (log && log.operation_details) {
      if (typeof log.operation_details === 'object') {
        return JSON.stringify(log.operation_details);
      }
      return log.operation_details;
    }
    return '格式化失败';
  }
};

// 日期范围变化处理
const onDateRangeChange = (value: [string, string] | null) => {
  if (value) {
    searchForm.value.start_date = value[0];
    searchForm.value.end_date = value[1];
  } else {
    searchForm.value.start_date = '';
    searchForm.value.end_date = '';
  }
};

// 按内容搜索询盘
const searchInquiriesByContent = async () => {
  // 重置日期筛选
  searchForm.value.start_date = '';
  searchForm.value.end_date = '';
  dateRange.value = null;
  currentPage.value = 1;
  // 确保只传递内容搜索参数
  const params = {
    page: currentPage.value,
    size: pageSize.value,
    search: searchForm.value.search,  // 只传递搜索参数，不传递日期参数
  };
  await loadInquiriesWithParams(params);
};

// 按日期搜索询盘
const searchInquiriesByDate = async () => {
  // 重置内容搜索
  searchForm.value.search = '';
  currentPage.value = 1;
  // 确保只传递日期参数
  const params = {
    page: currentPage.value,
    size: pageSize.value,
    start_date: searchForm.value.start_date,
    end_date: searchForm.value.end_date
  };
  await loadInquiriesWithParams(params);
};

// 带参数的加载询盘函数
const loadInquiriesWithParams = async (params: any) => {
  loading.value = true;
  try {
    const response = await request.get('/api/inquiries', { params });
    inquiries.value = response.list || [];
    total.value = response.total || 0;
  } catch (error) {
    console.error('加载询盘列表失败:', error);
    ElMessage.error('加载询盘列表失败');
  } finally {
    loading.value = false;
  }
};

// 重置搜索
const resetSearch = () => {
  searchForm.value = {
    search: '',
    area: '',
    contact_person: '',
    company_name: '',
    packaging_product: '',
    machine_type: '',
    inquiry_source: '',
    start_date: '',
    end_date: ''
  };
  dateRange.value = null;
  currentPage.value = 1;
  loadInquiries();
};

// 加载询盘列表
const loadInquiries = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value,
      search: searchForm.value.search,
      start_date: searchForm.value.start_date,
      end_date: searchForm.value.end_date
    };

    const response = await request.get('/api/inquiries', { params });
    inquiries.value = response.list || [];
    total.value = response.total || 0;
  } catch (error) {
    console.error('加载询盘列表失败:', error);
    ElMessage.error('加载询盘列表失败');
  } finally {
    loading.value = false;
  }
};

// 分页处理
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  loadInquiries();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  loadInquiries();
};

// 导出数据
const exportData = () => {
  ElMessage.info('数据导出功能待实现');
};

// 地区自动完成查询
const queryArea = (queryString: string, cb: (arg: any) => void) => {
  const results = queryString
    ? presetAreas.value.filter(area => area.toLowerCase().indexOf(queryString.toLowerCase()) === 0)
    : presetAreas.value;

  // 添加输入的值作为选项
  if (queryString && !results.includes(queryString)) {
    results.unshift(queryString);
  }

  cb(results.map(area => ({ value: area })));
};

// 来源自动完成查询
const querySource = (queryString: string, cb: (arg: any) => void) => {
  let results = queryString
    ? presetSources.value.filter(source => source.toLowerCase().indexOf(queryString.toLowerCase()) === 0)
    : presetSources.value;

  // 添加输入的值作为选项
  if (queryString && !results.includes(queryString)) {
    results.unshift(queryString);
  }

  // 同时包含预设值和用户输入
  results = [...new Set(results)]; // 去重

  cb(results.map(source => ({ value: source })));
};

// 比较表单值是否发生变化
const isFormChanged = (): boolean => {
  if (!initialInquiryForm.value) return false;

  // 比较所有字段
  return JSON.stringify(inquiryForm.value) !== JSON.stringify(initialInquiryForm.value);
};

// 对话框关闭处理
const handleDialogClose = (done: () => void) => {
  // 如果表单没有被修改过，直接关闭
  if (!isFormChanged()) {
    done();
    return;
  }

  ElMessageBox.confirm('表单内容已修改，确认关闭？', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
  .then(() => {
    done();
  })
  .catch(() => {
    // 取消操作
  });
};

// ===================== 沟通记录媒体文件处理 =====================

// 获取沟通记录的媒体文件
const getCommunicationMediaFiles = (source: any) => {
  // 如果是当前编辑的沟通记录（有本地预览文件）
  if (source === 'current') {
    return currentCommunicationMediaFiles.value.map((file: any) => ({
      url: file.url || file.file_path,
      thumb: file.thumb || file.thumb_path || file.file_path, // 如果没有缩略图，使用原图或文件路径
      id: file.id,  // 媒体文件ID，用于删除操作
      file_type: file.file_type,  // 文件类型：image或video
      is_local_preview: file.is_local_preview // 标记是否为本地预览
    }));
  }

  if (!source) return [];

  // 仅使用新的media_files字段
  if (source.media_files && Array.isArray(source.media_files)) {
    return source.media_files
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

// 获取沟通记录的媒体文件URL列表（用于预览）
const getCommunicationMediaUrls = (source: any) => {
  if (source === 'current') {
    // 对于当前编辑的沟通记录，只返回图片类型的URL用于预览
    return currentCommunicationMediaFiles.value
      .filter(file => file.file_type === 'image')
      .map(file => file.file_path);
  }

  return getCommunicationMediaFiles(source).map(media => media.url); // 总是返回原图用于预览
};

// 设置沟通记录上传预览组件引用
const setCommunicationUploadPreviewRef = (el: any) => {
  if (!editingCommunicationId.value && !currentCommunicationId.value) return;

  const commId = editingCommunicationId.value || currentCommunicationId.value;
  if (!commId) return;

  // 当el为null时，表示组件被卸载，应从引用中移除
  if (el) {
    communicationUploadPreviewRefs.value[commId] = el;
  } else {
    // 确保删除对应的沟通记录ID引用
    delete communicationUploadPreviewRefs.value[commId];
  }
};

// 处理沟通记录输入框的粘贴事件
const handleCommunicationInputPaste = (e: ClipboardEvent) => {
  try {
    // 检查是否有有效的沟通记录ID
    const commId = editingCommunicationId.value || currentCommunicationId.value;
    if (!commId) {
      ElMessage.error('无法粘贴媒体文件：未指定有效的沟通记录ID');
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
        const uploadPreviewRef = communicationUploadPreviewRefs.value[commId];
        if (uploadPreviewRef && uploadPreviewRef.addClipboardMedia) {
          uploadPreviewRef.addClipboardMedia(file);
          const fileType = file.type.startsWith('image/') ? '图片' : '视频';
          ElMessage.success(`已检测到${fileType}: ${file.name}，已添加到上传队列...`);
        } else {
          ElMessage.warning(`找不到沟通记录ID为 ${commId} 的上传组件，请确保该记录有上传组件`);
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

// 沟通记录媒体上传成功回调
const onCommunicationMediaUploadSuccess = async (files: File[], mediaFiles: any[] = []) => {
  ElMessage.success(`${files.length} 个媒体文件添加成功（待上传）`);

  // 为每个新添加的文件生成预览URL并添加到当前媒体文件列表
  const newMediaPreviews = files.map((file: File) => {
    const filePreviewUrl = URL.createObjectURL(file);
    const thumbPreviewUrl = file.type.startsWith('image/') ? filePreviewUrl : null;

    return {
      id: null, // 待上传文件没有ID
      file_name: file.name,
      file_path: filePreviewUrl, // 创建临时预览URL
      thumb_path: thumbPreviewUrl, // 图片使用原图作为缩略图
      url: filePreviewUrl, // 用于模板显示
      thumb: thumbPreviewUrl, // 用于模板显示
      file_type: file.type.startsWith('image/') ? 'image' : 'video',
      file_size: file.size,
      upload_time: new Date().toISOString(),
      is_local_preview: true // 标记为本地预览文件
    };
  });

  // 将预览文件添加到当前媒体文件列表
  currentCommunicationMediaFiles.value = [
    ...currentCommunicationMediaFiles.value,
    ...newMediaPreviews
  ];

  // 将文件添加到待上传列表
  pendingMediaFiles.value = [...pendingMediaFiles.value, ...files];

  // 如果有已上传的媒体文件信息（从服务器返回的），也添加到当前列表
  if (mediaFiles && mediaFiles.length > 0) {
    const uploadedMediaPreviews = mediaFiles.map((mediaFile: any) => ({
      id: mediaFile.id,
      file_name: mediaFile.file_name || files[mediaFiles.indexOf(mediaFile)].name,
      file_path: mediaFile.file_path,
      thumb_path: mediaFile.thumb_path,
      url: mediaFile.file_path, // 用于模板显示
      thumb: mediaFile.thumb_path || mediaFile.file_path, // 用于模板显示
      file_type: mediaFile.file_type,
      file_size: mediaFile.file_size,
      upload_time: mediaFile.upload_time,
      is_local_preview: false // 标记为服务器文件
    }));

    currentCommunicationMediaFiles.value = [
      ...currentCommunicationMediaFiles.value,
      ...uploadedMediaPreviews
    ];
  }
};

// 沟通记录媒体上传失败回调
const onCommunicationMediaUploadFailure = (error: any) => {
  console.error('沟通记录媒体文件上传失败：', error);
  ElMessage.error('沟通记录媒体文件上传失败');
};

// 上传剪贴板沟通记录媒体回调
const onUploadClipboardCommunicationMedia = async (response: any, file: File, commId: number) => {
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

    // 将文件添加到待上传列表
    pendingMediaFiles.value = [...pendingMediaFiles.value, file];

    // 显示成功消息
    const fileType = file.type.startsWith('image/') ? '图片' : '视频';
    ElMessage.success(`已添加${fileType}: ${file.name}（待上传）`);
  } catch (error) {
    console.error('添加剪贴板媒体失败:', error);
    ElMessage.error('添加剪贴板媒体失败');
  }
};

// 删除当前沟通记录中的媒体文件
const deleteCurrentCommunicationMedia = async (mediaIndex: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个媒体文件吗？删除后将无法恢复。', '确认删除', {
      type: 'warning'
    });

    // 边界校验
    if (mediaIndex < 0 || mediaIndex >= currentCommunicationMediaFiles.value.length) {
      ElMessage.error('媒体文件索引超出范围');
      return;
    }

    const mediaToDelete = currentCommunicationMediaFiles.value[mediaIndex];

    // 检查是否为本地预览文件，如果是则需要释放URL对象
    if (mediaToDelete.is_local_preview) {
      // 释放临时预览URL
      URL.revokeObjectURL(mediaToDelete.file_path);
      if (mediaToDelete.thumb_path) {
        URL.revokeObjectURL(mediaToDelete.thumb_path);
      }

      // 从待上传文件列表中移除对应的文件
      const fileIndex = pendingMediaFiles.value.findIndex((file, idx) => {
        // 根据文件名和大小进行匹配
        return file.name === mediaToDelete.file_name && file.size === mediaToDelete.file_size;
      });

      if (fileIndex !== -1) {
        // 创建新的待上传文件数组，排除被删除的文件
        const newPendingFiles = [...pendingMediaFiles.value];
        newPendingFiles.splice(fileIndex, 1);
        pendingMediaFiles.value = newPendingFiles;
      }
    } else if (mediaToDelete.id) {
      // 如果是服务器文件且有ID，尝试从服务器删除
      if (!editingCommunicationId.value) {
        // 如果是新建记录，直接从本地删除
        currentCommunicationMediaFiles.value.splice(mediaIndex, 1);
        ElMessage.success('媒体文件删除成功');
        return;
      }

      // 尝试从服务器删除
      const response: any = await request.delete(`/api/inquiries/communications/${editingCommunicationId.value}/media`, {
        data: { media_file_id: mediaToDelete.id }
      });

      if (response) {
        // 从本地列表中移除媒体文件
        currentCommunicationMediaFiles.value.splice(mediaIndex, 1);

        // 同时更新communications数组中对应记录的媒体文件信息
        if (editingCommunicationId.value) {
          const commIndex = communications.value.findIndex(c => c.id === editingCommunicationId.value);
          if (commIndex > -1) {
            // 从原数组中移除对应的媒体文件
            const updatedMediaFiles = communications.value[commIndex].media_files?.filter((file: any) => file.id !== mediaToDelete.id) || [];

            // 更新该记录的媒体文件信息
            communications.value[commIndex] = {
              ...communications.value[commIndex],
              media_files: updatedMediaFiles,
              images: updatedMediaFiles.filter((file: any) => file.file_type === 'image'),
              videos: updatedMediaFiles.filter((file: any) => file.file_type === 'video'),
              image_count: updatedMediaFiles.filter((file: any) => file.file_type === 'image').length,
              video_count: updatedMediaFiles.filter((file: any) => file.file_type === 'video').length
            };
          }
        }

        ElMessage.success('媒体文件删除成功');
        return;
      }
    }

    // 从本地列表中移除媒体文件
    currentCommunicationMediaFiles.value.splice(mediaIndex, 1);
    ElMessage.success('媒体文件删除成功');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除媒体文件失败:', error);
      ElMessage.error('删除媒体文件失败');
    }
  }
};
// 从沟通记录中删除媒体文件
const deleteMediaFromCommunication = async (communication: any, mediaIndex: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个媒体文件吗？删除后将无法恢复。', '确认删除', {
      type: 'warning'
    });

    // 解析当前媒体文件为结构化数组
    const currentMediaFiles = getCommunicationMediaFiles(communication);

    // 边界校验
    if (mediaIndex < 0 || mediaIndex >= currentMediaFiles.length) {
      ElMessage.error('媒体文件索引超出范围');
      return;
    }

    // 获取要删除的媒体文件信息
    const mediaToDelete = currentMediaFiles[mediaIndex];

    // 验证任务ID是否有效
    if (!mediaToDelete.id) {
      ElMessage.error('无法删除媒体文件：缺少媒体文件ID');
      return;
    }

    // 使用媒体文件ID进行删除
    const response: any = await request.delete(`/api/inquiries/communications/${communication.id}/media`, {
      data: { media_file_id: mediaToDelete.id }
    });

    if (response) {
      // 更新本地沟通记录数据
      const commIndex = communications.value.findIndex(c => c.id === communication.id);
      if (commIndex > -1) {
        const newCommunications = [...communications.value];

        // 从media_files数组中移除对应的媒体文件
        const updatedMediaFiles = newCommunications[commIndex].media_files?.filter((file: any) => file.id !== mediaToDelete.id) || [];

        newCommunications[commIndex] = {
          ...newCommunications[commIndex],
          media_files: updatedMediaFiles,
          images: updatedMediaFiles.filter((file: any) => file.file_type === 'image'),
          videos: updatedMediaFiles.filter((file: any) => file.file_type === 'video'),
          image_count: updatedMediaFiles.filter((file: any) => file.file_type === 'image').length,
          video_count: updatedMediaFiles.filter((file: any) => file.file_type === 'video').length
        };

        communications.value = newCommunications;
      }

      // 如果当前正在编辑的就是这个沟通记录，同时更新currentCommunicationMediaFiles
      if (editingCommunicationId.value === communication.id) {
        const updatedCurrentMediaFiles = currentCommunicationMediaFiles.value.filter((file: any) => file.id !== mediaToDelete.id);
        currentCommunicationMediaFiles.value = updatedCurrentMediaFiles;
      }

      ElMessage.success('媒体文件删除成功');
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除媒体文件失败:', error);
      ElMessage.error('删除媒体文件失败');
    }
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
// 加载沟通记录
const loadCommunications = async (inquiryId: number) => {
  try {
    const response = await request.get(`/api/inquiries/${inquiryId}/communications`);
    communications.value = response.list || [];
  } catch (error) {
    console.error('加载沟通记录失败:', error);
    ElMessage.error('加载沟通记录失败');
  }
};

// 显示沟通记录对话框
const showCommunicationDialog = async (inquiryId: number) => {
  currentInquiryId.value = inquiryId;
  await loadCommunications(inquiryId);
  communicationDialogVisible.value = true;
};

// 关闭沟通记录对话框
const closeCommunicationDialog = () => {
  communicationDialogVisible.value = false;
  communications.value = [];
  currentInquiryId.value = null;
};

// 显示添加沟通记录对话框
const showAddCommunicationDialog = () => {
  communicationDialogTitle.value = '添加沟通记录';
  editingCommunicationId.value = null;
  currentCommunicationId.value = -1; // 使用负数表示新的沟通记录
  communicationForm.value = {
    id: null,
    subject: '',
    content: '',
    communication_date: '',
    company_name: inquiryForm.value.company_name // Auto-populate from parent inquiry
  };
  currentCommunicationMediaFiles.value = []; // 重置媒体文件列表
  pendingMediaFiles.value = []; // 重置待上传文件列表
  addCommunicationDialogVisible.value = true;
};

// 编辑沟通记录
const editCommunication = (comm: any) => {
  communicationDialogTitle.value = '编辑沟通记录';
  editingCommunicationId.value = comm.id;
  currentCommunicationId.value = comm.id;
  communicationForm.value = {
    id: comm.id,
    subject: comm.subject,
    content: comm.content,
    communication_date: comm.communication_date,
    company_name: comm.company_name // Use the company_name from the communication record
  };
  // 设置当前沟通记录的媒体文件 - 使用服务器返回的文件信息
  currentCommunicationMediaFiles.value = (comm.media_files || []).map((file: any) => ({
    id: file.id,
    file_name: file.file_name,
    file_path: file.file_path,
    thumb_path: file.thumb_path,
    url: file.file_path,  // 添加url属性以匹配模板使用
    thumb: file.thumb_path || file.file_path,  // 添加thumb属性以匹配模板使用
    file_type: file.file_type,
    file_size: file.file_size,
    upload_time: file.upload_time,
    is_local_preview: false // 标记为服务器文件
  }));
  // 清空待上传文件列表
  pendingMediaFiles.value = [];
  addCommunicationDialogVisible.value = true;
};

// 提交沟通记录
const submitCommunication = async () => {
  if (!communicationFormRef.value) return;

  await communicationFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      if (!editingInquiryId.value) {
        ElMessage.error('请先保存询盘信息');
        return;
      }

      communicationSubmitting.value = true;
      try {
        let response;
        let communicationId;

        if (editingCommunicationId.value) {
          // 更新沟通记录
          response = await request.put(
            `/api/inquiries/${editingInquiryId.value}/communications/${editingCommunicationId.value}`,
            communicationForm.value
          );
          communicationId = editingCommunicationId.value;
          ElMessage.success('沟通记录更新成功');
        } else {
          // 创建沟通记录
          response = await request.post(
            `/api/inquiries/${editingInquiryId.value}/communications`,
            communicationForm.value
          );
          communicationId = response.id || response.data.id;
          ElMessage.success('沟通记录创建成功');
        }

        // 如果有待上传的媒体文件，则上传它们
        if (pendingMediaFiles.value.length > 0) {
          const formData = new FormData();

          // 添加所有待上传的文件
          pendingMediaFiles.value.forEach((file, index) => {
            formData.append('files', file);
          });

          // 添加通信ID
          formData.append('communication_id', communicationId.toString());

          try {
            // 上传媒体文件
            const mediaResponse: any = await request.post('/api/inquiries/upload-communication-media', formData, {
              headers: {
                'Content-Type': 'multipart/form-data'
              }
            });

            ElMessage.success(`成功上传 ${pendingMediaFiles.value.length} 个媒体文件`);

            // 清空待上传文件列表
            pendingMediaFiles.value = [];
          } catch (uploadError) {
            console.error('媒体文件上传失败:', uploadError);
            ElMessage.error('部分媒体文件上传失败，但沟通记录已保存');
            // 即使媒体上传失败，也要继续
          }
        }

        // 关闭对话框并重新加载列表
        addCommunicationDialogVisible.value = false;
        await loadCommunications(editingInquiryId.value);

        // 重置表单
        communicationForm.value = {
          id: null,
          subject: '',
          content: '',
          communication_date: '',
          company_name: ''
        };
        editingCommunicationId.value = null;

        // 释放本地预览文件的URL对象
        currentCommunicationMediaFiles.value.forEach(file => {
          if (file.is_local_preview && file.file_path) {
            URL.revokeObjectURL(file.file_path);
          }
          if (file.is_local_preview && file.thumb_path) {
            URL.revokeObjectURL(file.thumb_path);
          }
        });

        // 清空当前沟通记录的媒体文件和待上传文件
        currentCommunicationMediaFiles.value = [];
        pendingMediaFiles.value = [];
      } catch (error) {
        console.error('提交沟通记录失败:', error);
        ElMessage.error('提交沟通记录失败');
      } finally {
        communicationSubmitting.value = false;
      }
    } else {
      ElMessage.error('请填写必填项');
    }
  });
};

// 取消沟通记录操作
const cancelCommunication = () => {
  addCommunicationDialogVisible.value = false;
  communicationForm.value = {
    id: null,
    subject: '',
    content: '',
    communication_date: '',
    company_name: ''
  };
  editingCommunicationId.value = null;

  // 释放本地预览文件的URL对象
  currentCommunicationMediaFiles.value.forEach(file => {
    if (file.is_local_preview && file.file_path) {
      URL.revokeObjectURL(file.file_path);
    }
    if (file.is_local_preview && file.thumb_path) {
      URL.revokeObjectURL(file.thumb_path);
    }
  });

  currentCommunicationMediaFiles.value = [];
  pendingMediaFiles.value = []; // 清空待上传文件
};

// 删除沟通记录
const deleteCommunication = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这条沟通记录吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    if (!editingInquiryId.value) return;

    await request.delete(`/api/inquiries/${editingInquiryId.value}/communications/${id}`);
    ElMessage.success('沟通记录删除成功');
    await loadCommunications(editingInquiryId.value);
  } catch (error) {
    console.error('删除沟通记录失败:', error);
    if (error !== 'cancel') {
      ElMessage.error('删除沟通记录失败');
    }
  }
};
// 添加专门的日志跳转处理函数
const handleLogJump = (id: number) => {
  viewInquiry(id);
};

// 显示日志对话框
const showInquiryLogs = () => {
          if (!isAdmin.value) {    ElMessage.error('您没有权限查看日志');
    return;
  }
  // 先重置日志组件的状态，再显示对话框
  logDialogVisible.value = false;
  // 使用nextTick确保状态更新后再显示
  nextTick(() => {
    logDialogVisible.value = true;
  });
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

// 组件卸载时移除事件监听
onUnmounted(() => {
  document.removeEventListener('keydown', handleEscKey);
});

// 创建订单函数
const createOrder = async (inquiry: any) => {
  try {
    if (!inquiry.id) {
      ElMessage.error('询盘信息不完整，无法创建订单');
      return;
    }

    // // 检查询盘是否已关联订单
    // if (inquiryForm.value.is_associated) {
    //   ElMessage.error('该询盘已关联订单，不能重复创建');
    //   return;
    // }

    // 显示确认对话框
    await ElMessageBox.confirm(
      `确定要为询盘<br/><br>
      <strong>"${inquiry.area} - ${inquiry.company_name} ${inquiry.contact_person} ${inquiry.create_time}"</strong>
      <br><br>创建订单吗？`,
      '确认创建',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true, // 必须开启才能解析 <br/>
        center: true // 可选：让内容居中，更美观
      }
    );

    // 准备订单数据，使用询盘信息作为基础
    const orderData = {
      area: inquiry.area || '',
      customer_name: inquiry.company_name || '',
      customer_type: '', // 可以从用户输入获取
      order_time: new Date().toISOString().split('T')[0], // 使用当前日期作为下单时间
      ship_time: null, // 可以从用户输入获取
      ship_country: '', // 可以从用户输入获取
      contract_no: '', // 需要用户输入
      order_no: '', // 可以从用户输入获取
      machine_no: '', // 可以从用户输入获取
      machine_name: '包装机',
      machine_model: inquiry.machine_type || '', // 使用询盘中的机器类型
      machine_count: 1, // 默认数量为1
      unit: 'set',
      contract_amount: 0, // 需要用户输入
      deposit: 0, // 需要用户输入
      balance: 0, // 需要用户输入
      tax_rate: 13.0,
      tax_refund_amount: 0, // 需要用户输入
      currency_amount: 0, // 需要用户输入
      payment_received: 0, // 需要用户输入
      machine_cost: 0, // 需要用户输入
      net_profit: 0, // 需要用户输入
      proportionate_cost: 0, // 需要用户输入
      individual_cost: 0, // 需要用户输入
      gross_profit: 0, // 需要用户输入
      pay_type: 'T/T', // 默认支付方式
      commission: 0, // 需要用户输入
      latest_ship_date: null, // 需要用户输入
      expected_delivery: null, // 需要用户输入
      order_dept: '', // 可以从用户输入获取
      check_requirement: '', // 可以从用户输入获取
      attachment_imgs: '',
      attachment_videos: '',
      inquiry_id: inquiry.id // 关联当前询盘
    };

    // 创建订单
    const response = await request.post('/api/orders', orderData);

    // 由于request.ts会自动解包响应为res.data，所以response直接包含了后端返回的{code, msg, data}结构
    if (response && response.code === 200) {
      ElMessage.success('订单创建成功');

      // 更新询盘的关联状态
      inquiry.is_associated = true;

      // 关闭对话框
      inquiryDialogVisible.value = false;
    } else {
      // 如果没有code字段，可能返回的是直接的订单数据，表示成功
      if (response && typeof response === 'object' && !response.code) {
        // 假设这是一个成功的响应（包含了订单数据）
        ElMessage.success('订单创建成功');

        // 更新询盘的关联状态
        inquiry.is_associated = true;

        // 关闭对话框
        inquiryDialogVisible.value = false;
      } else {
        const errorMsg = response?.msg || '订单创建失败';
        ElMessage.error(errorMsg);
      }
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('创建订单失败:', error);
      let errorMsg = '创建订单失败';
      if (error.response?.data?.msg) {
        errorMsg = error.response.data.msg;
      } else if (error.message) {
        errorMsg = error.message;
      }
      ElMessage.error(errorMsg);
    }
  }
};





</script>

<style scoped>
.inquiry-list-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.filter-card {
  margin-bottom: 20px;
  padding: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.communication-section {
  margin-top: 20px;
}

.communication-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.communication-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: bold;
}

.communication-list {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 10px;
}

.communication-item {
  margin-bottom: 10px;
  padding: 0;
  border-radius: 15px;
}

.communication-content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.subject {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
  margin-left: 20px;
}

.communication-actions {
  display: flex;
  gap: 5px;
}

.communication-content {
  margin-left: 10px;
  margin-bottom: 8px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.5;
  padding: 15px 50px;
}

.communication-company {
  margin-left: 20px;
  margin-top: 5px;
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.communication-footer {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  font-size: 12px;
  color: #909399;
}

.date, .creator, .time {
  margin-right: 10px;
}

.no-communications {
  text-align: center;
  color: #909399;
  font-style: italic;
  padding: 20px;
}

.el-icon {
  font-size: 16px;
  cursor: pointer;
  margin-left: 10px;
}
.el-icon.edit {
  background-color: #317050;
  color: #FFFFFF;
  padding: 4px;
  border-radius: 3px;
}
.el-icon.delete {
  background-color: #c76767;
  color: #FFFFFF;
  padding: 4px;
  border-radius: 3px;
}

/* 日志样式 */
.log-container {
  max-height: 60vh;
  overflow-y: auto;
}

.statistics-card {
  margin-bottom: 15px;
  background-color: #f8f9fa;
}

.statistics-content {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 12px;
  color: #606266;
}

.stat-value {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-top: 2px;
}

.log-item {
  margin-bottom: 10px;
}

.log-company {
  display: flex;
  align-items: center;
  margin: 5px 0;
  font-size: 14px;
}

.company-label {
  font-weight: bold;
  color: #606266;
  margin-right: 8px;
  min-width: 40px;
}

.company-value {
  color: #303133;
  flex: 1;
}

.company-value:hover {
  color: #409EFF;
}

.stat-row {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #ebeef5;
}


.stat-item-unified {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-right: 30px;
  min-width: 80px;
}

.stat-label-unified {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value-unified {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.stat-value-unified.highlight {
  color: #e6a23c; /* 橙色，用于新增数据 */
  font-size: 20px;
}

.stat-value-unified.monthly {
  color: #909399; /* 灰色，用于月度数据 */
  font-size: 16px;
}

.stat-label-time {
  font-size: 12px;
  color: #909399;
  background-color: #f4f4f5;
  padding: 2px 8px;
  border-radius: 12px;
  margin-left: 10px;
}

.toggle-monthly-btn {
  margin-left: 10px;
  color: #909399;
}

.toggle-monthly-btn:hover {
  color: #409EFF;
}

.log-card {
  padding: 12px;
}

.log-toolbar {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 10px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.log-operation-type {
  display: inline-block;
  padding: 2px 8px;
  background-color: #ecf5ff;
  color: #409eff;
  border-radius: 4px;
  font-size: 12px;
}

.operation-type-text {
  font-weight: 500;
}

.log-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-time {
  font-size: 12px;
  color: #909399;
}

.log-btn {
  cursor: pointer;
  color:white;
  transition: color 0.2s;
}


.log-pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.log-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.log-user {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
}

.user-label {
  color: #909399;
}

.user-value {
  font-weight: 500;
}

.role-value {
  color: #909399;
  font-size: 12px;
}

.log-details {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  font-size: 13px;
  line-height: 1.4;
}

.details-label {
  color: #909399;
  flex-shrink: 0;
}

.details-value {
  color: #606266;
  word-break: break-word;
  flex: 1;
}

.opera-icon{
  font-size: 16px;
  cursor: pointer;
  margin-left: 10px;
  padding: 5px 12px;
  border-radius: 5px;
}

.opera-icon-big{
  font-size: 16px;
  cursor: pointer;
  margin-left: 10px;
  padding: 5px 12px;
  border-radius: 5px;
}



.el-icon{
  margin: 0px 5px;
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

/* 沟通记录媒体容器 */
.communication-media-container {
  margin-top: 10px;
  width:100%;
}

.task-img-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(85px, 1fr));  /* 横向自动填充布局 */
  gap: 10px;
  max-width: 100%;
  padding: 5px 10px;
  border:rgba(167, 167, 167, 0.1) solid 1px;
  background-color: rgba(167, 167, 167, 0.1);
  border-radius: 2px;
  grid-auto-rows: 85px; /* 固定行高 */
  align-items: start; /* 顶部对齐 */
  justify-items: center; /* 居中对齐 */
  min-width: 0; /* 允许内容压缩 */
}

/* 内容对齐样式额外，使内容列造和左边对齐 */
:deep(.el-form-item.media-upload-full-width .el-form-item__content) {
  flex-direction: column;
  align-items: flex-start;
}

/* 暴露响应式传煤对话框宽度优化 */
:deep(.communication-media-dialog .el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
}
</style>