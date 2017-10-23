/*
Navicat MySQL Data Transfer

Source Server         : hupo
Source Server Version : 50719
Source Host           : localhost:3306
Source Database       : web_crawler

Target Server Type    : MYSQL
Target Server Version : 50719
File Encoding         : 65001

Date: 2017-10-22 20:55:31
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for proxy
-- ----------------------------
DROP TABLE IF EXISTS `proxy`;
CREATE TABLE `proxy` (
  `url` varchar(30) NOT NULL,
  `ip` varchar(15) NOT NULL COMMENT 'IP',
  `port` varchar(5) NOT NULL DEFAULT '' COMMENT '端口',
  `address` varchar(25) DEFAULT NULL COMMENT '服务器地址',
  `types` varchar(5) DEFAULT '' COMMENT '类型',
  `speed` double DEFAULT NULL COMMENT '速度',
  `response_time` double DEFAULT NULL COMMENT '响应时间',
  `success_times` bigint(20) DEFAULT NULL COMMENT '成功次数',
  `failure_times` bigint(20) DEFAULT NULL COMMENT '失败次数',
  `source_url` varchar(255) DEFAULT NULL COMMENT '来源网站',
  `verification_time` double DEFAULT NULL COMMENT '验证时间',
  PRIMARY KEY (`url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
