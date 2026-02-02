import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, AtSign } from 'lucide-react';

/**
 * CommentBox - Input component for adding comments with @mention autocomplete
 * Features:
 * - Real-time @mention autocomplete dropdown
 * - Keyboard navigation (arrows, enter, escape)
 * - Visual highlighting of mentions
 * - Submit with loading state
 * - Character counter
 * - Filters employees to show only those with tasks in the same project
 */
export default function CommentBox({ onSubmit, employees = [], task = null, allTasks = [] }) {
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  
  // Autocomplete state
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [autocompleteQuery, setAutocompleteQuery] = useState('');
  const [filteredEmployees, setFilteredEmployees] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [cursorPosition, setCursorPosition] = useState(0);
  const [mentionStartPos, setMentionStartPos] = useState(null);
  
  const textareaRef = useRef(null);
  const autocompleteRef = useRef(null);

  const maxLength = 1000;
  const remainingChars = maxLength - comment.length;

  // Get employees who have tasks in the same project as current task
  const getEligibleEmployees = () => {
    if (!task || !task.projectId || !allTasks || allTasks.length === 0) {
      // If no task context, show all employees
      return employees;
    }

    // Find all employees assigned to tasks in this project
    const projectTasks = allTasks.filter(t => t.projectId === task.projectId);
    const employeeIds = new Set(
      projectTasks
        .map(t => t.assignedTo)
        .filter(id => id) // Remove null/undefined
    );

    // Filter employees to only those with tasks in this project
    return employees.filter(emp => employeeIds.has(emp.id || emp.employeeId));
  };

  const eligibleEmployees = getEligibleEmployees();

  // Detect @ mentions and trigger autocomplete
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const text = comment;
    const pos = cursorPosition;

    // Find if cursor is after an @
    let mentionStart = -1;
    for (let i = pos - 1; i >= 0; i--) {
      if (text[i] === '@') {
        mentionStart = i;
        break;
      }
      if (text[i] === ' ' || text[i] === '\n') {
        break;
      }
    }

    if (mentionStart >= 0) {
      const query = text.substring(mentionStart + 1, pos);
      
      // Filter eligible employees by name
      const filtered = eligibleEmployees.filter(emp =>
        emp.name.toLowerCase().includes(query.toLowerCase())
      );

      if (filtered.length > 0 && query.length >= 0) {
        setAutocompleteQuery(query);
        setFilteredEmployees(filtered);
        setMentionStartPos(mentionStart);
        setShowAutocomplete(true);
        setSelectedIndex(0);
      } else {
        setShowAutocomplete(false);
      }
    } else {
      setShowAutocomplete(false);
    }
  }, [comment, cursorPosition, employees]);

  // Handle clicking outside autocomplete
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (autocompleteRef.current && !autocompleteRef.current.contains(e.target)) {
        setShowAutocomplete(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const insertMention = (employee) => {
    if (mentionStartPos === null) return;

    const before = comment.substring(0, mentionStartPos);
    const after = comment.substring(cursorPosition);
    const mention = `@${employee.name}`;
    const newComment = before + mention + ' ' + after;
    
    setComment(newComment);
    setShowAutocomplete(false);
    
    // Set cursor after the mention
    const newCursorPos = mentionStartPos + mention.length + 1;
    setTimeout(() => {
      textareaRef.current?.focus();
      textareaRef.current?.setSelectionRange(newCursorPos, newCursorPos);
      setCursorPosition(newCursorPos);
    }, 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!comment.trim()) {
      return;
    }

    if (comment.length > maxLength) {
      setError(`Comment is too long (max ${maxLength} characters)`);
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const result = await onSubmit(comment.trim());
      
      if (result.success) {
        setComment(''); // Clear on success
      } else {
        setError(result.error || 'Failed to post comment');
      }
    } catch (err) {
      setError('An error occurred while posting your comment');
      console.error('Comment submission error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e) => {
    // Handle autocomplete navigation
    if (showAutocomplete) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < filteredEmployees.length - 1 ? prev + 1 : prev
        );
        return;
      }
      
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : 0);
        return;
      }
      
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        insertMention(filteredEmployees[selectedIndex]);
        return;
      }
      
      if (e.key === 'Escape') {
        e.preventDefault();
        setShowAutocomplete(false);
        return;
      }
    }
    
    // Submit on Ctrl/Cmd + Enter (only if autocomplete is not shown)
    if (!showAutocomplete && (e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  const handleChange = (e) => {
    setComment(e.target.value);
    setCursorPosition(e.target.selectionStart);
  };

  const handleClick = (e) => {
    setCursorPosition(e.target.selectionStart);
  };

  // Detect and count @mentions from eligible employees
  const mentionCount = (comment.match(/@[\w\s\.\-]+/g) || []).length;
  const mentionedEmployees = eligibleEmployees.filter(emp => {
    return comment.includes(`@${emp.name}`);
  });

  return (
    <div className="space-y-3">
      {/* Textarea with autocomplete */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={comment}
          onChange={handleChange}
          onClick={handleClick}
          onKeyDown={handleKeyDown}
          placeholder="Add a comment... Type @ to mention someone"
          rows={4}
          disabled={submitting}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none disabled:bg-gray-50 disabled:cursor-not-allowed"
        />
        
        {/* Autocomplete dropdown */}
        {showAutocomplete && filteredEmployees.length > 0 && (
          <div
            ref={autocompleteRef}
            className="absolute z-50 w-64 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto"
            style={{
              bottom: '100%',
              marginBottom: '0.5rem'
            }}
          >
            <div className="px-3 py-2 text-xs font-medium text-gray-500 border-b border-gray-200 flex items-center gap-2">
              <AtSign className="w-3 h-3" />
              <span>Mention employee</span>
            </div>
            {filteredEmployees.map((emp, index) => (
              <button
                key={emp.id}
                type="button"
                onClick={() => insertMention(emp)}
                onMouseEnter={() => setSelectedIndex(index)}
                className={`w-full px-3 py-2 text-left hover:bg-blue-50 transition-colors flex items-center gap-2 ${
                  index === selectedIndex ? 'bg-blue-50 border-l-2 border-blue-500' : ''
                }`}
              >
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 text-white font-medium text-sm flex-shrink-0">
                  {emp.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm text-gray-900 truncate">
                    {emp.name}
                  </div>
                  <div className="text-xs text-gray-500 truncate">
                    {emp.role}
                  </div>
                </div>
              </button>
            ))}
            <div className="px-3 py-2 text-xs text-gray-400 border-t border-gray-200 bg-gray-50">
              Use ↑↓ to navigate, Enter to select, Esc to cancel
            </div>
          </div>
        )}
        
        {/* Character counter */}
        <div className="absolute bottom-2 right-2 text-xs text-gray-400">
          {remainingChars < 100 && (
            <span className={remainingChars < 0 ? 'text-red-500 font-medium' : ''}>
              {remainingChars}
            </span>
          )}
        </div>
      </div>

      {/* Mention hint */}
      {mentionCount > 0 && (
        <div className="text-xs text-blue-600 bg-blue-50 px-3 py-2 rounded flex items-center gap-2">
          <AtSign className="w-4 h-4" />
          <span>
            <span className="font-medium">{mentionCount}</span> mention{mentionCount > 1 ? 's' : ''} detected. 
            Mentioned users will receive a WhatsApp notification.
          </span>
        </div>
      )}

      {/* Error message */}
        {error && (
          <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded">
            {error}
          </div>
        )}

        {/* Submit button */}
        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-500">
            Press <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs">
              Ctrl
            </kbd> + <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs">
              Enter
            </kbd> to submit
          </div>
          
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!comment.trim() || submitting || remainingChars < 0}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {submitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Posting...</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Comment</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
