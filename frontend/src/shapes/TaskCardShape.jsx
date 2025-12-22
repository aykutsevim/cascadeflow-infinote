import { BaseBoxShapeUtil, T, createShapeId } from 'tldraw';

// Priority color configuration
const priorityConfig = {
  urgent: { bg: '#fef2f2', border: '#ef4444', text: '#dc2626', label: 'URGENT' },
  high: { bg: '#fff7ed', border: '#f97316', text: '#ea580c', label: 'HIGH' },
  medium: { bg: '#eff6ff', border: '#3b82f6', text: '#2563eb', label: 'MEDIUM' },
  low: { bg: '#f0fdf4', border: '#22c55e', text: '#16a34a', label: 'LOW' },
};

// Shape props validation schema
export const taskCardShapeProps = {
  w: T.number,
  h: T.number,
  taskName: T.string,
  description: T.string,
  assignee: T.string,
  dueDate: T.string,
  priority: T.string,
};

export class TaskCardShapeUtil extends BaseBoxShapeUtil {
  static type = 'task-card';
  static props = taskCardShapeProps;

  getDefaultProps() {
    return {
      w: 280,
      h: 160,
      taskName: 'Untitled Task',
      description: '',
      assignee: '',
      dueDate: '',
      priority: 'medium',
    };
  }

  component(shape) {
    const { taskName, description, assignee, dueDate, priority } = shape.props;
    const config = priorityConfig[priority] || priorityConfig.medium;

    return (
      <div
        style={{
          width: '100%',
          height: '100%',
          backgroundColor: '#ffffff',
          borderRadius: '8px',
          border: `2px solid ${config.border}`,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          pointerEvents: 'all',
        }}
      >
        {/* Header with priority */}
        <div
          style={{
            backgroundColor: config.bg,
            borderBottom: `1px solid ${config.border}`,
            padding: '8px 12px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexShrink: 0,
          }}
        >
          <span
            style={{
              fontSize: '10px',
              fontWeight: '700',
              color: config.text,
              letterSpacing: '0.5px',
            }}
          >
            {config.label}
          </span>
          {dueDate && (
            <span
              style={{
                fontSize: '10px',
                color: '#6b7280',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
              {dueDate}
            </span>
          )}
        </div>

        {/* Content area */}
        <div
          style={{
            flex: 1,
            padding: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            overflow: 'hidden',
            minHeight: 0,
          }}
        >
          {/* Task name */}
          <h3
            style={{
              margin: 0,
              fontSize: '14px',
              fontWeight: '600',
              color: '#1f2937',
              lineHeight: '1.3',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
            }}
          >
            {taskName}
          </h3>

          {/* Description */}
          {description && (
            <p
              style={{
                margin: 0,
                fontSize: '11px',
                color: '#6b7280',
                lineHeight: '1.4',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
              }}
            >
              {description}
            </p>
          )}
        </div>

        {/* Footer with assignee */}
        {assignee && (
          <div
            style={{
              borderTop: '1px solid #e5e7eb',
              padding: '8px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: '#f9fafb',
              flexShrink: 0,
            }}
          >
            <div
              style={{
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                backgroundColor: config.border,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
                fontSize: '10px',
                fontWeight: '600',
              }}
            >
              {assignee.charAt(0).toUpperCase()}
            </div>
            <span
              style={{
                fontSize: '11px',
                color: '#4b5563',
                fontWeight: '500',
              }}
            >
              {assignee}
            </span>
          </div>
        )}
      </div>
    );
  }

  indicator(shape) {
    return (
      <rect
        width={shape.props.w}
        height={shape.props.h}
        rx={8}
        ry={8}
      />
    );
  }
}

// Helper function to create a task card shape
export function createTaskCardShape(task, x, y) {
  return {
    id: createShapeId(),
    type: 'task-card',
    x,
    y,
    props: {
      w: 280,
      h: 160,
      taskName: task.task_name || 'Untitled Task',
      description: task.description || '',
      assignee: task.assignee || '',
      dueDate: task.due_date || '',
      priority: task.priority || 'medium',
    },
  };
}
