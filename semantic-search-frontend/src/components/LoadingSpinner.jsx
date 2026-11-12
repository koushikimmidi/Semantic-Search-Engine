import "../styles/loading.css";

function LoadingSpinner({ loading }) {

    if (!loading) {
        return null;
    }

    return (

        <div className="loading-container">

            <div className="spinner"></div>

            <h2>Searching...</h2>

            <p>Please wait while the AI searches your documents.</p>

        </div>

    );

}

export default LoadingSpinner;