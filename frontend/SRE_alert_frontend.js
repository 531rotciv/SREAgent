(function(){
  const {useState, useRef} = React;

  function App(){
    // The API URL for the backend server that handles the investigation requests. 
    // Hardcoded to localhost for development purposes. In a production environment, 
    // this should come from configurations or secrets.
    const API_URL = "http://localhost:8000";

    // Stores all investigation event text
    // except the final "complete" event.
    const [investigationOutput, setInvestigationOutput] = useState([]);

    // Stores the final synthesis from the "complete" event.
    const [result, setResult] = useState('');

    // Controls which output is displayed.
    const [activeView, setActiveView] = useState('investigation');

    // Tracks whether a streaming investigation is in progress.
    const [streaming, setStreaming] = useState(false);
    const [status, setStatus] = useState('idle');

    const controllerRef = useRef(null);

    // Generates a random alert ID for testing purposes.
    function randomAlertId(){
      const n = Math.floor(Math.random() * 5) + 1;
      return `alert-${String(n).padStart(3, '0')}`;
    }

    // Returns a user-friendly status message based on the current investigation status.
    function statusMessage(status){
      switch ((status || '').toLowerCase()) {

        case 'starting':
          return 'Starting investigation...';

        case 'progress':
          return 'Investigating the incident...';

        case 'tool_call':
          return 'Checking system data...';

        case 'tool_result':
          return 'Reviewing evidence...';

        case 'investigation_complete':
          return 'Investigation complete.';

        case 'synthesis_start':
          return 'Putting together the final assessment...';

        case 'complete':
          return 'Investigation complete.';

        case 'error':
          return 'Something went wrong during the investigation.';

        default:
          return 'Nothing running right now. Press the button above to start.';
      }
    }

    // Handles the generation of an investigation based on a random alert ID.
    async function handleGenerate(){

      // Cancel any existing request.
      if (controllerRef.current){
        controllerRef.current.abort();
        controllerRef.current = null;
      }

      // Reset previous investigation.
      setInvestigationOutput([]);
      setResult('');
      setActiveView('investigation');
      setStatus('starting');

      const alert_id = randomAlertId();

      const controller = new AbortController();
      controllerRef.current = controller;

      setStreaming(true);

      // Fetch the investigation data from the backend API.
      // The backend is expected to stream newline-delimited JSON events.
      // Each event contains a "type" and "text" field.
      // The frontend processes these events in real-time, updating the UI accordingly.
      try {

        const res = await fetch(
          `${API_URL}/sre-model/alerts/${alert_id}`,
          {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json'
            },
            signal: controller.signal,
          }
        );

        if (!res.ok){

          const text = await res.text();

          // If the response is not OK, log the error and update the investigation output with the error message.
          setInvestigationOutput(
            (o) => [
              ...o,
              `[error ${res.status}] ${text}`
            ]
          );

          setStatus('error');

          return;
        }

        const reader = res.body.getReader();
        const dec = new TextDecoder();

        // HTTP chunks do not necessarily correspond
        // to complete JSON objects.
        let buffer = '';

        // Read the response stream in chunks, processing each chunk as it arrives.
        // The buffer accumulates data until a complete JSON object (delimited by newlines) is formed.
        while (true){

          const {done, value} = await reader.read();

          if (done) break;

          buffer += dec.decode(value, {stream: true});

          // Backend sends newline-delimited JSON.
          const lines = buffer.split(/\r?\n/);

          // Keep an incomplete final line for
          // the next chunk.
          buffer = lines.pop();

          // Process each complete line as a JSON object.
          for (const line of lines){

            if (!line.trim()) continue;

            try {

              const response = JSON.parse(line);

              const type = response.type;
              const text = response.text;

              console.log("type:", type);
              console.log("text:", text);

              // Update status based on the event type.
              setStatus(type);

              if (typeof text !== 'string'){
                continue;
              }

              // ------------------------------------------
              // Final synthesis
              // ------------------------------------------

              if (type === 'complete'){

                setResult(text);

                // Automatically switch to the result tab.
                setActiveView('result');

              }

              // ------------------------------------------
              // Investigation event
              // ------------------------------------------

              else {

                setInvestigationOutput(
                  (o) => [...o, text]
                );

              }

            } catch (error) {

              console.error(
                "Failed to parse JSON:",
                line,
                error
              );

            }
          }
        }

        // ------------------------------------------------
        // Process any final JSON object left in the buffer
        // ------------------------------------------------
        
        // After the stream ends, there may still be a final JSON object in the buffer that hasn't been processed yet.
        // This ensures that any remaining data is handled appropriately.
        if (buffer.trim()){

          try {

            const response = JSON.parse(buffer);

            const type = response.type;
            const text = response.text;

            console.log("type:", type);
            console.log("text:", text);

            setStatus(type);

            if (typeof text === 'string'){

              if (type === 'complete'){

                setResult(text);
                setActiveView('result');

              } else {

                setInvestigationOutput(
                  (o) => [...o, text]
                );

              }
            }

          } catch (error) {

            console.error(
              "Failed to parse final JSON:",
              buffer,
              error
            );

          }
        }

      } catch (err){

        if (err.name === 'AbortError'){

          setInvestigationOutput(
            (o) => [...o, 'Investigation cancelled.']
          );

          setStatus('idle');

        } else {

          setInvestigationOutput(
            (o) => [...o, '[error] ' + err.message]
          );

          setStatus('error');

        }

      } finally {

        setStreaming(false);
        controllerRef.current = null;

      }
    }

    // Returns a color code based on the current investigation status.
    function statusColor(status){

      switch ((status || '').toLowerCase()) {

        case 'complete':
        case 'healthy':
          return '#16a34a';

        case 'error':
          return '#dc2626';

        case 'starting':
          return '#3b82f6';

        case 'progress':
        case 'tool_call':
        case 'tool_result':
        case 'synthesis_start':
          return '#d98b47';

        default:
          return '#d98b47';
      }
    }

    // Convert the investigation event array
    // into one string for the textarea.
    const investigationText =
      investigationOutput.join('\n\n');

    // The Result tab should only become available
    // after the final synthesis has arrived.
    const isComplete = result !== '';

    return React.createElement(
      'div',
      {
        style: {
          minHeight: '100vh',
          background: '#f5f4fc',
          padding: '24px 32px',
          boxSizing: 'border-box',
          fontFamily:
            'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
          color: '#17141f'
        }
      },

      // ==================================================
      // Main container
      // ==================================================

      React.createElement(
        'div',
        {
          style: {
            maxWidth: 1140,
            margin: '0 auto'
          }
        },

        // ==================================================
        // Hero
        // ==================================================

        React.createElement(
          'div',
          {
            style: {
              background: '#6b5bd6',
              borderRadius: 17,
              padding: '26px 36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
              minHeight: 122,
              marginBottom: 36
            }
          },

          React.createElement(
            'div',
            null,

            React.createElement(
              'div',
              {
                style: {
                  fontSize: 23,
                  fontWeight: 700,
                  color: '#fff',
                  marginBottom: 7
                }
              },
              'Try it out'
            ),

            React.createElement(
              'div',
              {
                style: {
                  fontSize: 19,
                  color: 'rgba(255,255,255,0.78)'
                }
              },
              'See how the assistant handles a problem, start to finish'
            )
          ),

          React.createElement(
            'button',
            {
              onClick: handleGenerate,
              disabled: streaming,

              style: {
                padding: '16px 34px',
                minWidth: 274,
                border: 'none',
                borderRadius: 12,
                background: '#d98b47',
                color: '#fff',
                fontSize: 20,
                fontWeight: 700,
                cursor: streaming
                  ? 'not-allowed'
                  : 'pointer',
                opacity: streaming ? 0.7 : 1
              }
            },
            streaming
              ? 'Investigating...'
              : 'Simulate a problem'
          )
        ),

        // ==================================================
        // Status
        // ==================================================

        React.createElement(
          'div',
          {
            style: {
              background: '#fff',
              border: '1px solid #e2dff0',
              borderRadius: 16,
              padding: '22px 27px',
              display: 'flex',
              alignItems: 'center',
              marginBottom: 30,
              minHeight: 72,
              boxSizing: 'border-box'
            }
          },

          React.createElement(
            'div',
            {
              style: {
                width: 15,
                height: 15,
                borderRadius: '50%',
                background: statusColor(status),
                marginRight: 15,
                flexShrink: 0
              }
            }
          ),

          React.createElement(
            'div',
            {
              style: {
                fontSize: 20,
                color: '#211d29'
              }
            },
            statusMessage(status)
          )
        ),

        // ==================================================
        // Tabs
        // ==================================================

        React.createElement(
          'div',
          {
            style: {
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 12,
              marginBottom: 18
            }
          },

          // ------------------------------------------------
          // Investigation tab
          // ------------------------------------------------

          React.createElement(
            'button',
            {
              onClick: () => setActiveView('investigation'),

              style: {
                height: 66,
                borderRadius: 13,
                border:
                  activeView === 'investigation'
                    ? 'none'
                    : '1px solid #e3e0ed',
                background:
                  activeView === 'investigation'
                    ? '#6b5bd6'
                    : '#faf9fd',
                color:
                  activeView === 'investigation'
                    ? '#fff'
                    : '#b6b3c2',
                fontSize: 21,
                fontWeight: 700,
                cursor: 'pointer'
              }
            },
            "What's it's checking"
          ),

          // ------------------------------------------------
          // Result tab
          // ------------------------------------------------

          React.createElement(
            'button',
            {
              onClick: () => {
                if (isComplete){
                  setActiveView('result');
                }
              },

              disabled: !isComplete,

              style: {
                height: 66,
                borderRadius: 13,
                border:
                  activeView === 'result'
                    ? 'none'
                    : '1px solid #e3e0ed',
                background:
                  activeView === 'result'
                    ? '#6b5bd6'
                    : '#faf9fd',
                color:
                  activeView === 'result'
                    ? '#fff'
                    : '#b6b3c2',
                fontSize: 21,
                fontWeight: 700,
                cursor: isComplete
                  ? 'pointer'
                  : 'not-allowed'
              }
            },
            'What it found'
          )
        ),

        // ==================================================
        // Output card
        // ==================================================

        React.createElement(
          'div',
          {
            style: {
              background: '#fff',
              border: '1px solid #e2dff0',
              borderRadius: 16,
              padding: 32,
              boxSizing: 'border-box'
            }
          },

          // ------------------------------------------------
          // Investigation textarea
          // ------------------------------------------------

          activeView === 'investigation' &&

          React.createElement(
            'textarea',
            {
              value: investigationText,
              readOnly: true,

              style: {
                width: '100%',
                height: '330px',
                padding: 16,
                boxSizing: 'border-box',
                resize: 'none',
                overflowY: 'auto',
                border: 'none',
                outline: 'none',
                background: '#fff',
                fontFamily: 'monospace',
                fontSize: 15,
                lineHeight: 1.65,
                color: '#34303d'
              },

              placeholder:
                'Nothing to show yet. Start a run to see the assistant work through it step by step.'
            }
          ),

          // ------------------------------------------------
          // Result textarea
          // ------------------------------------------------

          activeView === 'result' &&

          React.createElement(
            'textarea',
            {
              value: result,
              readOnly: true,

              style: {
                width: '100%',
                height: '330px',
                padding: 16,
                boxSizing: 'border-box',
                resize: 'none',
                overflowY: 'auto',
                border: 'none',
                outline: 'none',
                background: '#fff',
                fontFamily:
                  'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                fontSize: 16,
                lineHeight: 1.7,
                color: '#34303d'
              },

              placeholder:
                'No result available yet.'
            }
          )
        )
      )
    );
  }

  const root = ReactDOM.createRoot(
    document.getElementById('root')
  );

  root.render(
    React.createElement(App)
  );

})();
