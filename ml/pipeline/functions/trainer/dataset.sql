select
    word_count
    ,title
from
    awsblogs.ml.post_length
order by
    created_at desc
limit
    10000;