import React from 'react';
import { Empty } from 'antd';

const PlaceholderPage = ({ title, description = '该功能正在开发中，敬请期待' }) => {
  return (
    <div style={{ padding: '80px 24px', textAlign: 'center' }}>
      <Empty
        description={
          <div>
            <h2 style={{ fontSize: '24px', fontWeight: 600, marginBottom: '8px', color: '#262626' }}>
              {title}
            </h2>
            <p style={{ fontSize: '14px', color: '#999' }}>{description}</p>
          </div>
        }
      />
    </div>
  );
};

export default PlaceholderPage;
