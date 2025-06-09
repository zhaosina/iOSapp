-- =====================================
-- 数据库：toefl_app
-- =====================================

-- 注：若使用 Django 自动建表，可忽略本部分，文档仅作参考。
-- 若需要手动建表，则先删除已有同名表：
DROP TABLE IF EXISTS api_practicerecord;
DROP TABLE IF EXISTS api_speakingquestion;
DROP TABLE IF EXISTS api_dailyplan;

-- 1. 题库表：api_speakingquestion
CREATE TABLE `api_speakingquestion` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `task_type` TINYINT NOT NULL COMMENT '任务类型：1=Task1；2=Task2',
  `prompt_text` VARCHAR(2000) NOT NULL COMMENT '题目描述',
  `sample_answer` TEXT NULL COMMENT '示范答案',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_task_type` (`task_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='托福口语题库表';

-- 2. 练习记录表：api_practicerecord
CREATE TABLE `api_practicerecord` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '外键：auth_user.id',
  `question_id` BIGINT NOT NULL COMMENT '外键：api_speakingquestion.id',
  `audio_url` VARCHAR(500) NULL COMMENT '上传到 media/practice_audio 的相对路径',
  `text_answer` TEXT NULL COMMENT '文本答案（可选）',
  `overall_score` DECIMAL(4,1) NULL COMMENT '总评分 0-30',
  `pronunciation_score` DECIMAL(4,1) NULL COMMENT '发音维度评分 0-30',
  `fluency_score` DECIMAL(4,1) NULL COMMENT '流利度维度评分 0-30',
  `vocabulary_score` DECIMAL(4,1) NULL COMMENT '词汇维度评分 0-30',
  `coherence_score` DECIMAL(4,1) NULL COMMENT '逻辑维度评分 0-30',
  `feedback_json` JSON NULL COMMENT 'Qwen-Omni 返回的详细反馈 JSON',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_user_created_at` (`user_id`, `created_at`),
  CONSTRAINT `fk_practice_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_practice_question` FOREIGN KEY (`question_id`) REFERENCES `api_speakingquestion` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户练习记录表';

-- 3. 每日计划表：api_dailyplan
CREATE TABLE `api_dailyplan` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '外键：auth_user.id',
  `plan_date` DATE NOT NULL COMMENT '计划对应的日期',
  `tasks_json` JSON NOT NULL COMMENT '今日计划题目列表与重点维度，例如 [{"question_id":5,"focus":"fluency"},...]',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_user_plan_date` (`user_id`,`plan_date`),
  CONSTRAINT `fk_dailyplan_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户每日专项练习计划表';
