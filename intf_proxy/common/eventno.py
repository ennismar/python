#coding:utf-8
__author__ = 'Ennis'

#事件号定义
EVENT_NO_DEF = 20000

EVENT_TCP_DEF = EVENT_NO_DEF + 500
IOT_PF_TO_TCPINTF_REQ = EVENT_TCP_DEF + 1
IOT_PF_TO_TCPINTF_RSP = EVENT_TCP_DEF + 2
IOT_TCPINTF_TO_PF_REQ = EVENT_TCP_DEF + 3
IOT_TCPINTF_TO_PF_RSP = EVENT_TCP_DEF + 4

IOT_SOCK_TCPINTF_TO_PF = EVENT_TCP_DEF + 5

EVENT_HTTP_DEF = EVENT_NO_DEF + 600
IOT_PF_TO_HTTPINTF_REQ = EVENT_HTTP_DEF + 1
IOT_PF_TO_HTTPINTF_RSP = EVENT_HTTP_DEF + 2
IOT_HTTPINTF_TO_PF_REQ = EVENT_HTTP_DEF + 3
IOT_HTTPINTF_TO_PF_RSP = EVENT_HTTP_DEF + 4