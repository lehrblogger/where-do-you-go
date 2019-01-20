var TweetThisLink = {
    shorten : function(e) {
        e.preventDefault();
        var url = $('#tweet_link').attr('name');
        BitlyClient.shorten(url, 'TweetThisLink.response');
    },
    response : function(data) {
        var bitly_link = null;
        for (var r in data.results) {
            bitly_link = data.results[r]['shortUrl'];
            break;
        }
        var tweet_text = 'Where do I go? See a heat map of my @foursquare check-ins at '
        document.location = "http://twitter.com/home?status=" + encodeURIComponent(tweet_text + bitly_link + ' #WDYG');
    }
}

$(document).ready(function() {
  $('#tweet_link').live('click', TweetThisLink.shorten);
});