import React from 'react';
import { Layout, Menu, Badge } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { MODEL_NAV, THEME } from '../config/modelNav';

const { Header, Sider, Content } = Layout;

const ModelLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Build menu items from MODEL_NAV
  const menuItems = MODEL_NAV.map((group, groupIndex) => {
    return {
      type: 'group',
      label: group.groupTitle,
      children: group.items.map((item) => ({
        key: item.path,
        label: (
          <span style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>{item.label}</span>
            {item.badge && (
              <Badge
                count={item.badge}
                style={{
                  backgroundColor: item.badge === '演示' ? '#52c41a' :
                                   item.badge === '优化' ? '#1890ff' :
                                   item.badge === '特定' ? '#faad14' : '#999',
                  fontSize: '10px',
                  height: '16px',
                  lineHeight: '16px',
                  borderRadius: '8px',
                  padding: '0 6px',
                }}
              />
            )}
          </span>
        ),
        onClick: () => navigate(item.path),
      })),
    };
  });

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Top Header */}
      <Header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          background: '#fff',
          borderBottom: '1px solid #f0f0f0',
          padding: '0 24px',
        }}
      >
        <div
          style={{
            fontSize: '20px',
            fontWeight: 600,
            color: THEME.primaryColor,
            marginRight: '24px',
            cursor: 'pointer',
          }}
          onClick={() => navigate('/model')}
        >
          Quanta
        </div>
        <Badge
          count="DEMO"
          style={{
            backgroundColor: '#52c41a',
            marginLeft: '8px',
            fontSize: '11px',
            height: '18px',
            lineHeight: '18px',
          }}
        />
        <div style={{ flex: 1 }} />
        <div style={{ display: 'flex', gap: '16px', fontSize: '14px', color: '#666' }}>
          <span>文档</span>
          <span>工具</span>
          <span>客服</span>
          <span>租户管理</span>
          <span style={{ color: THEME.primaryColor, fontWeight: 500 }}>宁德时代</span>
        </div>
      </Header>

      <Layout>
        {/* Dark Sidebar */}
        <Sider
          width={200}
          theme="dark"
          style={{
            background: THEME.sidebarBg,
            overflow: 'auto',
            height: 'calc(100vh - 64px)',
            position: 'fixed',
            left: 0,
            top: 64,
            bottom: 0,
          }}
        >
          {/* Platform Title */}
          <div
            style={{
              padding: '16px',
              color: '#fff',
              fontSize: '16px',
              fontWeight: 600,
              borderBottom: '1px solid rgba(255,255,255,0.1)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span>✦</span>
            <span>模型平台</span>
          </div>

          {/* Navigation Menu */}
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            style={{
              background: THEME.sidebarBg,
              border: 'none',
            }}
          />
        </Sider>

        {/* Main Content */}
        <Layout style={{ marginLeft: 200 }}>
          <Content
            style={{
              padding: '24px',
              background: THEME.contentBg,
              minHeight: 'calc(100vh - 64px)',
            }}
          >
            <div
              style={{
                background: '#fff',
                padding: '24px',
                borderRadius: '8px',
                minHeight: '100%',
              }}
            >
              <Outlet />
            </div>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default ModelLayout;
