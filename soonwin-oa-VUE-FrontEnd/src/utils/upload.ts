import request from '@/utils/request';

/**
 * 上传文件
 * @param file 文件对象
 * @param targetPath 目标路径（可选，如果不提供则上传到临时位置）
 * @returns 上传结果
 */
export const uploadFile = async (file: File, targetPath?: string) => {
  const formData = new FormData();
  formData.append('file', file);
  
  if (targetPath) {
    formData.append('target_path', targetPath);
  }
  
  try {
    const response: any = await request.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response;
  } catch (error) {
    throw error;
  }
};

/**
 * 分块上传文件
 * @param file 文件对象
 * @param chunkSize 分块大小，默认为5MB
 * @returns 上传结果
 */
export const uploadFileInChunks = async (file: File, chunkSize: number = 5 * 1024 * 1024, targetPath?: string) => {
  const totalChunks = Math.ceil(file.size / chunkSize);
  const fileIdentifier = `${file.name}-${file.size}-${new Date().getTime()}`;
  
  const uploadPromises = [];
  
  for (let i = 0; i < totalChunks; i++) {
    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, file.size);
    const chunk = file.slice(start, end);
    
    const formData = new FormData();
    formData.append('chunk', chunk);
    formData.append('chunk_index', i.toString());
    formData.append('total_chunks', totalChunks.toString());
    formData.append('filename', file.name);
    formData.append('file_identifier', fileIdentifier);
    
    // 如果是最后一块，同时提供目标路径
    if (i === totalChunks - 1 && targetPath) {
      formData.append('target_path', targetPath);
    }
    
    uploadPromises.push(
      request.post('/api/upload/chunk', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    );
  }
  
  try {
    // 顺序上传各分块
    for (let i = 0; i < uploadPromises.length; i++) {
      const result = await uploadPromises[i];
      if (i === uploadPromises.length - 1) {
        return result; // 返回最终结果
      }
    }
  } catch (error) {
    throw error;
  }
};

/**
 * 移动文件
 * @param sourcePath 源文件路径
 * @param targetPath 目标文件路径
 * @returns 移动结果
 */
export const moveFile = async (sourcePath: string, targetPath: string) => {
  try {
    const response: any = await request.post('/api/upload/move', {
      source_path: sourcePath,
      target_path: targetPath
    });
    return response;
  } catch (error) {
    throw error;
  }
};

/**
 * 删除文件
 * @param filePath 文件路径
 * @returns 删除结果
 */
export const deleteFile = async (filePath: string) => {
  try {
    const response: any = await request.post('/api/upload/delete', {
      file_path: filePath
    });
    return response;
  } catch (error) {
    throw error;
  }
};

/**
 * 生成安全的文件名
 * @param filename 原始文件名
 * @returns 安全的文件名
 */
export const sanitizeFilename = (filename: string): string => {
  // 移除Windows不支持的字符
  let sanitized = filename.replace(/[<>:"/\\|?*]/g, '_');
  
  // 限制文件名长度
  const lastDotIndex = sanitized.lastIndexOf('.');
  if (lastDotIndex !== -1) {
    const name = sanitized.substring(0, lastDotIndex);
    const ext = sanitized.substring(lastDotIndex);
    
    if (name.length > 100) {
      sanitized = name.substring(0, 100) + ext;
    }
    if (ext.length > 10) {
      sanitized = name + ext.substring(0, 10);
    }
  } else if (sanitized.length > 100) {
    sanitized = sanitized.substring(0, 100);
  }
  
  return sanitized;
};